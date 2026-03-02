from abc import abstractmethod
from typing import Any, TypeVar, overload
from src.util.result import Result
from src.template.front_mater_meta import FrontMatterMeta
from .protocol_upgrade_rule import ProtocolUpgradeRule

T = TypeVar("T")


class RuleUpgrade(ProtocolUpgradeRule):
    def __init__(self) -> None:
        self.__cache = {}

    @abstractmethod
    def get_rule_id(self) -> str: ...

    @abstractmethod
    def get_description(self) -> str: ...

    def get_order(self) -> int:
        """Gets the order that the rule is to be run"""
        return 100  # default

    def should_run(self, fm_artifact, fm_template, registry) -> bool:
        required_fields = getattr(self, "required_fields", None)
        if required_fields:
            return any(fm_artifact.has_field(f) for f in required_fields)
        return True

    def _get_registry_data(self, registry: dict[str, Any]) -> dict[str, Any]:
        """
        Retrieves metadata from the registry or returns the registry itself if metadata is not found.
        This method attempts to extract the 'metadata' key from the provided registry dictionary.
        If the 'metadata' key doesn't exist, it returns the entire registry dictionary as a fallback.

        This method also caches the retrieved metadata for future access, so subsequent calls with the same registry will return the cached data without needing to access the registry again.

        Args:
            registry (dict[str, Any]): A dictionary containing registry information, potentially
                with a 'metadata' key that holds the relevant data.
        Returns:
            dict[str, Any]: The metadata dictionary if it exists in the registry, otherwise
                the complete registry dictionary.
        """
        key = "rule_metadata"
        if self._has_item(key):
            item = self._get_item(key, dict[str, Any])
            return item

        reg = registry.get("metadata", registry)
        self.__cache[key] = reg
        return reg

    @overload
    def _get_item(self, key: str) -> Any: ...

    @overload
    def _get_item(self, key: str, expected_type: type[T]) -> T: ...

    def _get_item(self, key: str, expected_type: type[T] | None = None) -> Any | T:
        """
        Retrieves an item from the cache or registry.
        This method first checks if the specified key exists in the internal cache. If it does, it returns the cached value.
        If the key is not found in the cache, it attempts to retrieve the value from the registry using the get_registry_data method.
        The retrieved value is then stored in the cache for future access before being returned.
        Args:
            key (str): The key for which to retrieve the value from the cache or registry.
            expected_type (type[T], optional): An optional type hint for the expected return type.
        Returns:
            Any | T: The value associated with the specified key, either from the cache or the registry.
        """
        if key not in self.__cache:
            raise KeyError(f"Rule cache does not contain key '{key}'.")
        return self.__cache[key]

    def _has_item(self, key: str) -> bool:
        """
        Checks if a key exists in the cache or registry.
        This method checks if the specified key exists in the internal cache. If it does, it returns True.
        If the key is not found in the cache, it checks the registry using the get_registry_data method to see if the key exists there.
        Args:
            key (str): The key to check for existence in the cache or registry.
        Returns:
            bool: True if the key exists in either the cache or the registry, False otherwise.
        """

        return key in self.__cache

    @abstractmethod
    def apply(
        self,
        fm_artifact: FrontMatterMeta,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> Result[FrontMatterMeta, None] | Result[None, Exception]: ...
