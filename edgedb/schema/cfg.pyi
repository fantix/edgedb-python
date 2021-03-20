import edgedb.schema.std

class AbstractConfig(ConfigObject):
    __init__: Any = ...
    __annotations__: Any = ...
    __dataclass_fields__: Any = ...
    __dataclass_params__: Any = ...
    __edb_abstract__: Any = ...
    __edb_bases__: Any = ...
    __edb_name__: Any = ...
    __eq__: Any = ...
    __hash__: Any = ...
    allow_dml_in_functions: bool = ...
    default_statistics_target: str = ...
    effective_cache_size: str = ...
    effective_io_concurrency: str = ...
    listen_addresses: str = ...
    listen_port: int = ...
    query_work_mem: str = ...
    shared_buffers: str = ...

class Auth(ConfigObject):
    __init__: Any = ...
    __annotations__: Any = ...
    __dataclass_fields__: Any = ...
    __dataclass_params__: Any = ...
    __edb_abstract__: Any = ...
    __edb_bases__: Any = ...
    __edb_name__: Any = ...
    __eq__: Any = ...
    __hash__: Any = ...
    comment: str = ...
    priority: int = ...
    user: str = ...

class AuthMethod(ConfigObject):
    __init__: Any = ...
    __annotations__: Any = ...
    __dataclass_fields__: Any = ...
    __dataclass_params__: Any = ...
    __edb_abstract__: Any = ...
    __edb_bases__: Any = ...
    __edb_name__: Any = ...
    __eq__: Any = ...
    __hash__: Any = ...

class Config(AbstractConfig):
    __init__: Any = ...
    __annotations__: Any = ...
    __dataclass_fields__: Any = ...
    __dataclass_params__: Any = ...
    __edb_abstract__: Any = ...
    __edb_bases__: Any = ...
    __edb_name__: Any = ...
    __eq__: Any = ...
    __hash__: Any = ...

class ConfigObject(edgedb.schema.std.BaseObject):
    __init__: Any = ...
    __annotations__: Any = ...
    __dataclass_fields__: Any = ...
    __dataclass_params__: Any = ...
    __edb_abstract__: Any = ...
    __edb_bases__: Any = ...
    __edb_name__: Any = ...
    __eq__: Any = ...
    __hash__: Any = ...

class DatabaseConfig(AbstractConfig):
    __init__: Any = ...
    __annotations__: Any = ...
    __dataclass_fields__: Any = ...
    __dataclass_params__: Any = ...
    __edb_abstract__: Any = ...
    __edb_bases__: Any = ...
    __edb_name__: Any = ...
    __eq__: Any = ...
    __hash__: Any = ...

class SCRAM(AuthMethod):
    __init__: Any = ...
    __annotations__: Any = ...
    __dataclass_fields__: Any = ...
    __dataclass_params__: Any = ...
    __edb_abstract__: Any = ...
    __edb_bases__: Any = ...
    __edb_name__: Any = ...
    __eq__: Any = ...
    __hash__: Any = ...

class SystemConfig(AbstractConfig):
    __init__: Any = ...
    __annotations__: Any = ...
    __dataclass_fields__: Any = ...
    __dataclass_params__: Any = ...
    __edb_abstract__: Any = ...
    __edb_bases__: Any = ...
    __edb_name__: Any = ...
    __eq__: Any = ...
    __hash__: Any = ...

class Trust(AuthMethod):
    __init__: Any = ...
    __annotations__: Any = ...
    __dataclass_fields__: Any = ...
    __dataclass_params__: Any = ...
    __edb_abstract__: Any = ...
    __edb_bases__: Any = ...
    __edb_name__: Any = ...
    __eq__: Any = ...
    __hash__: Any = ...
