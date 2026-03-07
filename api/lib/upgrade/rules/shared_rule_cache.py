from typing import Any, TypeVar, Generic
from api.lib.protocols import ProtocolRulesCache

C = TypeVar("C")  # Cache type variable


class SharedRuleCache(Generic[C], ProtocolRulesCache[C]):
    """
    Shared metadata cache for all rules during a single upgrade run.
    Supports namespaced and global key-value storage.

    Supports `in` and `[]` access for global keys, and a `namespace` method for retrieving namespaced data.
    """

    def __init__(self):
        self._store: dict[str, C] = {}

    def get_item(self, key: str) -> C:
        """Retrieve an item from the cache by key. Raises KeyError if the key does not exist."""
        if key not in self._store:
            raise KeyError(f"SharedRuleCache: key '{key}' not found.")
        return self._store[key]

    def has_item(self, key: str) -> bool:
        """Check if the cache contains a specific key."""
        return key in self._store

    def set_item(self, key: str, value: Any) -> None:
        """Set a value in the cache for a specific key."""
        self._store[key] = value

    def get(self, key: str, default: C | None = None) -> C | None:
        """Retrieve an item from the cache by key, returning a default value if the key does not exist."""
        return self._store.get(key, default)

    def all(self) -> dict[str, C]:
        """Return a shallow copy of the cache."""
        return dict(self._store)

    def clear(self) -> None:
        """Clear all items from the cache."""
        self._store.clear()

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def __getitem__(self, key: str) -> C:
        return self.get_item(key)

    def namespace(self, ns: str) -> dict[str, C]:
        """
        Retrieve all key-value pairs belonging to a specific namespace.
        This method filters the internal store to return only items whose keys
        start with the given namespace prefix (formatted as "ns::"). The namespace
        prefix is stripped from the returned keys.

        Args:
            ns (str): The namespace identifier to filter by.

        Returns:
            dict[str, C]: A dictionary containing all key-value pairs in the
                specified namespace, with the namespace prefix removed from the keys.

        Example:
            If the store contains {"user::name": "John", "user::age": 30, "config::debug": True}
            and namespace("user") is called, it returns {"name": "John", "age": 30}.
        """

        prefix = f"{ns}::"
        return {
            k[len(prefix) :]: v for k, v in self._store.items() if k.startswith(prefix)
        }
