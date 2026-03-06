from typing import runtime_checkable, TypeVar
from typing import Protocol


T = TypeVar("T")


@runtime_checkable
class ProtocolRulesCache(Protocol[T]):
    """Protocol defining the interface for a rules cache."""

    def get_item(self, key: str) -> T:
        """Retrieve an item from the cache by key. Raises KeyError if the key does not exist."""
        ...

    def has_item(self, key: str) -> bool:
        """Check if the cache contains a specific key."""
        ...

    def set_item(self, key: str, value: T) -> None:
        """Set a value in the cache for a specific key."""
        ...

    def get(self, key: str, default: T | None = None) -> T | None:
        """Retrieve an item from the cache by key, returning a default value if the key does not exist."""
        ...

    def all(self) -> dict[str, T]:
        """Return a shallow copy of the cache."""
        ...

    def clear(self) -> None:
        """Clear all items from the cache."""
        ...

    def __contains__(self, key: str) -> bool: ...

    def __getitem__(self, key: str) -> T: ...

    def namespace(self, ns: str) -> dict[str, T]:
        """Retrieve all key-value pairs belonging to a specific namespace."""
        ...


class ProtocolRulesCacheFactory(Protocol[T]):
    """Protocol for rule class constructors."""

    def __call__(self, *args, **kwargs) -> ProtocolRulesCache[T]: ...
