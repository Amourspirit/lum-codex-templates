from abc import abstractmethod
from typing import Any, TypeVar, Generic, cast
from src.template.front_mater_meta import FrontMatterMeta
from ..upgrade_result import UpgradeResult as Result
from ..exceptions import UpgradeError
from .protocol_upgrade_rule import ProtocolUpgradeRule
from .protocol_rules_cache import ProtocolRulesCache

C = TypeVar("C")  # Cache type variable


class RuleUpgrade(ProtocolUpgradeRule[C], Generic[C]):
    def __init__(self, shared_cache: ProtocolRulesCache[C]) -> None:
        self._local_cache: dict[str, Any] = {}
        self._shared_cache = shared_cache

    @abstractmethod
    def get_rule_id(self) -> str: ...

    @abstractmethod
    def get_description(self) -> str: ...

    def get_order(self) -> int:
        """Gets the order that the rule is to be run"""
        return 100  # default

    def should_run(
        self,
        fm_artifact: FrontMatterMeta,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> bool:
        """Gets if the rule should be run based on the artifact, template, and registry.
        By default, returns True.

        This method should be overridden when a rule requires more complex logic to determine if it should be applied.
        For example, a rule that only applies to certain template types might check the template's metadata for a specific field or value.

        Args:
            fm_artifact (FrontMatterMeta): The frontmatter metadata of the artifact being upgraded.
            fm_template (FrontMatterMeta): The frontmatter metadata of the template being used for the upgrade.
            registry (dict[str, Any]): A dictionary containing registry information.

        Returns:
            bool: True if the rule should be applied, False otherwise.
        """
        template_required_fields = getattr(self, "template_required_fields", None)
        if template_required_fields:
            return any(fm_template.has_field(f) for f in template_required_fields)

        registry_keys = getattr(self, "registry_required", None)
        if registry_keys:
            reg_data = self._get_registry_data(
                registry
            )  # Ensure registry data is cached
            return all(k in reg_data for k in registry_keys)
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
        key = "registry_metadata"
        if key in self.shared_cache:
            item = cast(dict[str, Any], self.shared_cache[key])
            return item

        reg = registry.get("metadata", registry)
        self.shared_cache.set_item("registry_metadata", reg)
        return reg

    def _local_get(self, key: str) -> Any:
        """
        Retrieve an item from the local cache by its key.

        Args:
            key (str): The key identifying the cached item to retrieve.

        Returns:
            Any: The cached value associated with the given key.

        Raises:
            KeyError: If the specified key does not exist in the local cache.
        """

        if key not in self._local_cache:
            raise KeyError(f"Rule cache does not contain key '{key}'.")
        return self._local_cache[key]

    def _local_has(self, key: str) -> bool:
        """Return True if key exists in this rule’s local cache."""
        return key in self._local_cache

    def _local_set(self, key: str, value: Any) -> None:
        """
        Set an item in the local cache.

        Args:
            key (str): The key to store the value under in the local cache.
            value (Any): The value to be stored in the local cache.

        Returns:
            None
        """

        self._local_cache[key] = value

    @property
    def rule_name(self) -> str:
        """Human-friendly rule name."""
        desc = self.get_description()
        return desc if desc and desc.strip() else self.get_rule_id()

    # region Shared cache (namespaced)
    @property
    def shared_cache(self) -> ProtocolRulesCache[C]:
        """Provides access to the shared cache for all rules."""
        return self._shared_cache

    def shared_set(self, key: str, value: C) -> None:
        """
            Set a value in the shared cache.

        Args:
            key (str): The key to store the value under.
                The key should not contain any namespace prefix,
                as it will be automatically namespaced using the
                rule ID to avoid conflicts with other rules.
            value (Any): The value to store in the shared cache.

        Returns:
            None

        Notes:
            The key is automatically namespaced using the rule ID to avoid conflicts
            with other rules. The actual cache key will be in the format:
            "{rule_id}::{key}"
        """

        namespaced = f"{self.get_rule_id()}::{key}"
        self.shared_cache.set_item(namespaced, value)

    def shared_get(self, key: str, default: C | None = None) -> C | None:
        """
        Retrieve a value from the shared cache using a key.

        Args:
            key (str): The key to retrieve from the shared cache.
                The key should not contain any namespace prefix, as it will be automatically namespaced.
            default (Any, optional): The default value to return if the key is not found. Defaults to None.

        Returns:
            Any: The value associated with the key, or the default value if the key does not exist.
        """

        namespaced = f"{self.get_rule_id()}::{key}"
        return self.shared_cache.get(namespaced, default)

    # endregion Shared cache (namespaced)

    @abstractmethod
    def apply(
        self,
        fm_artifact: FrontMatterMeta,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> Result[FrontMatterMeta, None] | Result[None, UpgradeError]: ...
