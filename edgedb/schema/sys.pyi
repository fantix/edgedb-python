import dataclasses
from typing import Any
import edgedb.schema.schema
import edgedb.schema.std

@dataclasses.dataclass
class Database(SystemObject):
    name: str = ...

@dataclasses.dataclass
class ExtensionPackage(SystemObject):
    script: str = ...

@dataclasses.dataclass
class Role(edgedb.schema.schema.InheritingObject, SystemObject):
    is_superuser: bool = ...
    name: str = ...
    password: str = ...
    superuser: bool = ...

@dataclasses.dataclass
class SystemObject(edgedb.schema.schema.AnnotationSubject): ...

class TransactionIsolation(edgedb.schema.std.anyenum): ...

class VersionStage(edgedb.schema.std.anyenum): ...
