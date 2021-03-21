import dataclasses as _dataclasses
import functools as _functools
import importlib as _importlib
import itertools as _itertools
import sys as _sys
import textwrap as _textwrap
from importlib.abc import MetaPathFinder, Loader
from importlib.util import spec_from_loader, module_from_spec


class BaseModelMeta(type):
    pass


class BaseObject(metaclass=BaseModelMeta):
    __edb_abstract__ = True

    def __new__(cls, *args, **kwargs):
        if cls.__edb_abstract__:
            raise TypeError(f"Abstract {cls} cannot be instantiated.")
        return super().__new__(cls, *args, **kwargs)


class Object(BaseObject):
    pass


class anyscalar:
    __edb_abstract__ = True


class EdgeDBModuleImporter(MetaPathFinder, Loader):
    introspect_modules = _textwrap.dedent(
        """\
        SELECT schema::Module {
            name,
            builtin,
        }
        """
    )
    introspect_object_types = _textwrap.dedent(
        """\
        SELECT schema::ObjectType {
            __type__: { name },
            name,
            abstract,
            bases: { name },
            properties := (
                SELECT .properties {
                    name,
                    cardinality,
                    required,
                    readonly,
                    default,
                    expr,
                    target: { name, __type__: { name } },
                }
                FILTER @owned
            ),
            links := (
                SELECT .links {
                    name,
                    target: { name },
                }
            ),
        }
        """
    )
    introspect_scalar_types = _textwrap.dedent(
        """\
        SELECT schema::ScalarType {
            __type__: { name },
            name,
            abstract,
            bases: { name },
        }
        """
    )
    prevent_inheritance = {("schema::ConsistencySubject", "schema::AnnotationSubject")}
    predefined_types = {
        "std::BaseObject": BaseObject,
        "std::Object": Object,
        "std::anyscalar": anyscalar,
    }
    type_mapping = {
        "std::int16": int,
        "std::int64": int,
        "std::str": str,
        "std::bool": bool,
    }

    def __init__(self, namespace=None):
        self._namespace = namespace
        self.invalidate_caches()

    def _to_py_names(self, name):
        module_name, type_name = name.split("::")
        namespace = self._namespace
        if self._modules[module_name]:
            namespace = __package__
        if namespace:
            module_name = f"{namespace}.{module_name}"
        return module_name, type_name

    def _add_modules(self, modules):
        for module in modules:
            self._modules[module.name] = module.builtin
            self._types.setdefault(self._to_py_names(module.name + "::x")[0], [])

    def _add_definitions(self, definitions):
        for dfn in definitions:
            self._definitions[dfn.name] = dfn
            module_name, type_name = self._to_py_names(dfn.name)
            self._types.setdefault(module_name, []).append((type_name, dfn.name))

    def _update_all(self, *, install=True):
        method = set.union if install else set.difference
        sys_all = set(name for name, builtin in self._modules.items() if builtin)
        schema_mod = _importlib.import_module(__package__)
        schema_mod.__all__ = tuple(method(set(schema_mod.__all__), sys_all))
        if self._namespace:
            user_all = set(self._modules).difference(sys_all)
            if user_all:
                user_mod = _importlib.import_module(self._namespace)
                user_mod.__all__ = tuple(
                    method(set(getattr(user_mod, "__all__", [])), user_all)
                )

    def _get_metaclass(self, bases):
        mros = [
            (set(x) - {None})
            for x in (
                _itertools.zip_longest(*(type(base).__mro__[::-1] for base in bases))
            )
        ]
        if any(len(x) > 1 for x in mros):
            raise TypeError("metaclass conflict")
        return mros[-1].pop()

    def _create_objecttype(self, definition, *, name, bases, dict_):
        metaclass = self._get_metaclass(bases)
        return metaclass(name, bases, dict_)

    def _create_scalartype(self, definition, *, name, bases, dict_):
        metaclass = self._get_metaclass(bases)
        return metaclass(name, bases, dict_)

    def _get_deps_objecttype(self, definition):
        types = []
        for prop in definition.properties:
            if prop.target.__type__.name not in {
                "schema::ObjectType",
                "schema::ScalarType",
            }:
                continue
            if prop.target.name not in self._py_types:
                types.append(prop.target.name)
        return types

    def _get_deps_scalartype(self, definition):
        return []

    def _complete_objecttype(self, t, definition):
        for prop in definition.properties:
            if prop.target.__type__.name in {
                "schema::ObjectType",
                "schema::ScalarType",
            }:
                target_name = prop.target.name
                type_ = self._py_types[target_name]
                t.__annotations__[prop.name] = self.type_mapping.get(target_name, type_)
                setattr(t, prop.name, type_)
        _dataclasses.dataclass(t)

    def _complete_scalartype(self, t, definition):
        pass

    def invalidate_caches(self):
        self._modules = {}  # std -> True (builtin)
        self._definitions = {}  # std::int32 -> <object>
        self._types = {}  # edgedb.schema.std -> [(int32, std::int32), ...]
        self._py_modules = {}  # edgedb.schema.std -> <module>
        self._py_types = {}  # std::int32 -> <type>

    def find_spec(self, fullname, *args, **kwargs):
        if fullname in self._types:
            return spec_from_loader(fullname, self)

    def create_module(self, spec):
        try:
            return self._py_modules[spec.name]
        except KeyError:
            spec.loader = None
            try:
                rv = self._py_modules[spec.name] = module_from_spec(spec)
                rv.__edb_name__ = spec.name.split(".")[-1]
                rv.__edb_builtin__ = self._modules[rv.__edb_name__]
                return rv
            finally:
                spec.loader = self

    def exec_module(self, module):
        module.__all__ = all_ = []
        stack = []  # [std::int32, std::int64, ...]

        for type_name, name in self._types[module.__name__]:
            all_.append(type_name)
            if type_name not in module.__dict__:
                stack.append(name)

        stack.reverse()
        partial_types = []

        while stack:
            name = stack[-1]
            if name in self._py_types:
                stack.pop()
                continue

            bases = []
            definition = self._definitions[name]
            edb_bases = []
            missing_bases = False
            for base in definition.bases:
                base_name = base.name
                edb_bases.append(base_name)
                if (name, base_name) in self.prevent_inheritance:
                    continue
                if base_name in self._py_types:
                    bases.append(self._py_types[base_name])
                else:
                    stack.append(base_name)
                    missing_bases = True
            if missing_bases:
                continue

            module_name, type_name = self._to_py_names(name)
            cur_module = self.create_module(self.find_spec(module_name))
            dict_ = {
                "__module__": module_name,
                "__edb_name__": name,
                "__edb_bases__": edb_bases,
                "__edb_abstract__": definition.abstract,
                "__annotations__": {},
            }
            more_deps = []
            if name in self.predefined_types:
                t = self.predefined_types[name]
                dict_.pop("__module__")
                for k, v in dict_.items():
                    setattr(t, k, v)
            else:
                type_ = definition.__type__.name.split("::")[-1].lower()
                creator = _functools.partial(
                    getattr(self, "_create_" + type_),
                    definition,
                    name=type_name,
                    dict_=dict_,
                )
                try:
                    t = creator(bases=tuple(bases))
                except TypeError:
                    bases = tuple(
                        base
                        for base in bases
                        if base
                        not in set(
                            b
                            for base in bases
                            for i, b in enumerate(base.mro())
                            if i > 0
                        )
                    )
                    t = creator(bases=bases)

                partial_types.append((t, type_, definition))
                more_deps = getattr(self, "_get_deps_" + type_)(definition)

            self._py_types[name] = cur_module.__dict__[type_name] = t
            stack.pop()
            stack.extend(more_deps)

        for t, type_, definition in partial_types:
            getattr(self, "_complete_" + type_)(t, definition)

        return module

    def get_module(self, fullname):
        return self.exec_module(self.create_module(self.find_spec(fullname)))

    def all(self, *, builtin=False):
        return tuple(
            module
            for module, is_builtin in self._modules.items()
            if is_builtin == builtin
        )

    def install(self):
        self.uninstall()
        _sys.meta_path.append(self)
        self._update_all(install=True)

    @classmethod
    def uninstall(cls):
        if _sys.meta_path:
            for i in range(len(_sys.meta_path) - 1, -1, -1):
                if type(_sys.meta_path[i]).__name__ == cls.__name__:
                    _sys.meta_path[i]._update_all(install=False)
                    del _sys.meta_path[i]

    def introspect(self, pool_or_conn):
        self._add_modules(pool_or_conn.query(self.introspect_modules))
        self._add_definitions(pool_or_conn.query(self.introspect_scalar_types))
        self._add_definitions(pool_or_conn.query(self.introspect_object_types))
        self.install()
        return self

    async def async_introspect(self, pool_or_conn):
        self._add_modules(await pool_or_conn.query(self.introspect_modules))
        self._add_definitions(await pool_or_conn.query(self.introspect_scalar_types))
        self._add_definitions(await pool_or_conn.query(self.introspect_object_types))
        self.install()
        return self


__all__ = ("BaseModelMeta", "BaseObject", "Object", "anyscalar", "EdgeDBModuleImporter")

from edgedb import connect as _connect

EdgeDBModuleImporter().introspect(_connect("authub"))
