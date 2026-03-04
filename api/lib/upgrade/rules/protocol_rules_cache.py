from typing import Any, runtime_checkable
from typing import Protocol


@runtime_checkable
class ProtocolRulesCache(Protocol):
    """Protocol defining the interface for a rules cache."""

    def get_item(self, key: str) -> Any:
        """Retrieve an item from the cache by key. Raises KeyError if the key does not exist."""
        ...

    def has_item(self, key: str) -> bool:
        """Check if the cache contains a specific key."""
        ...

    def set_item(self, key: str, value: Any) -> None:
        """Set a value in the cache for a specific key."""
        ...

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve an item from the cache by key, returning a default value if the key does not exist."""
        ...

    def all(self) -> dict[str, Any]:
        """Return a shallow copy of the cache."""
        ...

    def clear(self) -> None:
        """Clear all items from the cache."""
        ...

    def __contains__(self, key: str) -> bool: ...

    def __getitem__(self, key: str) -> Any: ...

    def namespace(self, ns: str) -> dict[str, Any]:
        """Retrieve all key-value pairs belonging to a specific namespace."""
        ...


class ProtocolRulesCacheFactory(Protocol):
    """Protocol for rule class constructors."""

    def __call__(self, *args, **kwargs) -> ProtocolRulesCache: ...
