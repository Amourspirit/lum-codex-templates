from typing import Any


class SharedRuleCache:
    """
    Shared metadata cache for all rules during a single upgrade run.
    Supports namespaced and global key-value storage.
    """

    def __init__(self):
        self._store: dict[str, Any] = {}

    def get_item(self, key: str) -> Any:
        if key not in self._store:
            raise KeyError(f"SharedRuleCache: key '{key}' not found.")
        return self._store[key]

    def has_item(self, key: str) -> bool:
        return key in self._store

    def set_item(self, key: str, value: Any) -> None:
        self._store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def all(self) -> dict[str, Any]:
        """Return a shallow copy of the cache."""
        return dict(self._store)

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def __getitem__(self, key: str) -> Any:
        return self.get_item(key)

    def namespace(self, ns: str) -> dict[str, Any]:
        prefix = f"{ns}::"
        return {
            k[len(prefix) :]: v for k, v in self._store.items() if k.startswith(prefix)
        }
