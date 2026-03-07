from typing import Generic, Protocol, TypeVar, runtime_checkable
from .protocol_rules_cache import ProtocolRulesCache

C = TypeVar("C")  # Cache type variable


@runtime_checkable
class ProtocolSharedCache(Protocol, Generic[C]):
    @property
    def shared_cache(self) -> ProtocolRulesCache[C]: ...
    def shared_set(self, key: str, value: C) -> None: ...
    def shared_get(self, key: str, default: C | None = None) -> C | None: ...


class SharedCacheFactory(Protocol, Generic[C]):
    """Protocol for shared cache class constructors."""

    def __call__(
        self, shared_cache: ProtocolRulesCache[C]
    ) -> ProtocolSharedCache[C]: ...
