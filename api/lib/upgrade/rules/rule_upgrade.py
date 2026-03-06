from abc import abstractmethod
from typing import Any, TypeVar, Generic, cast
from ..exceptions import MissingKeyError, UpgradeError
from ..protocols import ProtocolRulesCache
from ..protocols import ProtocolUpgradeRuleSharedCache
from ..upgrade_result import SeverityKind
from ..upgrade_result import UpgradeResult as UpgradeResult
from src.template.front_mater_meta import FrontMatterMeta

C = TypeVar("C")  # Cache type variable


class RuleUpgrade(ProtocolUpgradeRuleSharedCache[C], Generic[C]):
    RULE_ORDER = 100

    def __init__(self, shared_cache: ProtocolRulesCache[C]) -> None:
        self._local_cache: dict[str, Any] = {}
        self._shared_cache = shared_cache

    @abstractmethod
    def get_rule_id(self) -> str: ...

    @abstractmethod
    def get_description(self) -> str: ...

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

    def _get_field_data(
        self, reg_data: dict[str, Any], field: str
    ) -> UpgradeResult[dict[str, Any], None] | UpgradeResult[None, MissingKeyError]:
        """
        Retrieve field data from registry configuration.
        Attempts to extract a specific field from the registry data dictionary.
        If the field is missing, returns a failure Result with a MissingKeyError.

        Args:
            reg_data (dict[str, Any]): The registry data dictionary containing configuration.
            field (str): The name of the field to retrieve from the registry data.

        Returns:
            Result[dict[str, Any], None] | Result[None, MissingKeyError]:
                - On success: A Result containing the field data dictionary.
                - On failure: A Result containing a MissingKeyError with CRITICAL severity
                  and context information about the missing field.

        Raises:
            None: Errors are returned as Result objects rather than raised.
        """

        reg: dict[str, Any] | None = reg_data.get(field, None)
        if reg is None:
            return UpgradeResult.failure(
                MissingKeyError(
                    f"Registry Missing {field} configuration",
                    field,
                    f"Registry must specify {field} configuration for upgrade.",
                ),
                severity=SeverityKind.CRITICAL,
                payload={
                    "missing_field": field,
                    "context": "registry",
                },
            )
        return UpgradeResult.success(reg)

    def _get_allowed_values(
        self, field_data: dict[str, Any], field: str
    ) -> UpgradeResult[set[str], None] | UpgradeResult[None, UpgradeError]:
        """
        Retrieve and validate the allowed values for a given field from field data.
        This method extracts the set of allowed values from the field data dictionary
        and validates that at least one allowed value exists. If no allowed values are
        found, it returns a critical error result.

        Args:
            field_data (dict[str, Any]): Dictionary containing field configuration,
                including an optional "allowed_values" key with a list of valid values.
            field (str): The name of the field for which allowed values are being retrieved.

        Returns:
            Result[set[str], None] | Result[None, UpgradeError]:
                - On success: A Result containing a set of allowed values for the field.
                - On failure: A Result containing an UpgradeError with CRITICAL severity,
                  indicating that no allowed values were found in the registry for the field.

        Note:
            The failure payload includes the field name and issue type for debugging purposes.
        """

        allowed = set(field_data.get("allowed_values", []))
        if len(allowed) == 0:
            return UpgradeResult.failure(
                UpgradeError(
                    f"Registry Missing allowed_values for {field}",
                    field,
                    f"Registry must specify allowed values for {field}.",
                ),
                severity=SeverityKind.CRITICAL,
                payload={
                    "field": field,
                    "issue": "no_allowed_values",
                },
            )
        return UpgradeResult.success(allowed)

    def _get_default_value(
        self, field_data: dict[str, Any], field: str, allowed: set[str] | None = None
    ) -> UpgradeResult[str, None] | UpgradeResult[None, UpgradeError]:
        """
        Retrieve and validate the default value for a field from field data.
        This method extracts the default value from the provided field data dictionary
        and validates it against the allowed values if specified.
        Args:
            field_data: Dictionary containing field metadata including the default_value.
            field: Name of the field being validated.
            allowed: Optional set of allowed values for the field. If provided, the
                default value must be present in this set.
        Returns:
            UpgradeResult containing either:
                - Success with the validated default value (str)
                - Failure with an UpgradeError if:
                    * No default_value is found in field_data (CRITICAL severity)
                    * The default value is not in the allowed set (CRITICAL severity)
        Raises:
            None: All errors are returned as UpgradeResult failures rather than raised.
        """

        default = cast(str | None, field_data.get("default_value", None))
        if default is None:
            return UpgradeResult.failure(
                UpgradeError(
                    f"Registry Missing default_value for {field} and not default provided by artifact",
                    field,
                    f"Registry must specify a default value for {field}.",
                ),
                severity=SeverityKind.CRITICAL,
                payload={
                    "field": field,
                    "issue": "no_default_value",
                },
            )

        if allowed is not None and default not in allowed:
            return UpgradeResult.failure(
                UpgradeError(
                    f"Default {field} '{default}' not allowed by registry",
                    field,
                    f"Allowed values: {allowed}",
                ),
                severity=SeverityKind.CRITICAL,
                payload={
                    "default_value": default,
                    "allowed_values": list(allowed),
                    "context": "invalid_registry_default",
                },
            )
        return UpgradeResult.success(default)

    def _get_reg_required_fields(
        self, reg_data: dict[str, Any]
    ) -> UpgradeResult[list[str], None] | UpgradeResult[None, UpgradeError]:
        fields: dict[str, Any] | None = reg_data.get("fields", None)
        key = "_required_fields"
        if key in self._local_cache:
            item = cast(list[str], self._local_cache[key])
            return UpgradeResult.success(item)

        if fields is None:
            return UpgradeResult.failure(
                UpgradeError(
                    "Registry Missing fields configuration",
                    "fields",
                    "Registry must specify fields configuration for upgrade.",
                ),
                severity=SeverityKind.CRITICAL,
                payload={
                    "missing_field": "fields",
                    "context": "registry",
                },
            )
        required_fields = [f for f, v in fields.items() if v.get("required", False)]
        self._local_cache[key] = required_fields
        return UpgradeResult.success(required_fields)

    def _get_reg_all_fields(
        self, reg_data: dict[str, Any]
    ) -> UpgradeResult[set[str], None] | UpgradeResult[None, UpgradeError]:
        fields: dict[str, Any] | None = reg_data.get("fields", None)
        key = "_all_fields"
        if key in self._local_cache:
            item = cast(set[str], self._local_cache[key])
            return UpgradeResult.success(item)

        if fields is None:
            return UpgradeResult.failure(
                UpgradeError(
                    "Registry Missing fields configuration",
                    "fields",
                    "Registry must specify fields configuration for upgrade.",
                ),
                severity=SeverityKind.CRITICAL,
                payload={
                    "missing_field": "fields",
                    "context": "registry",
                },
            )
        all_fields = set(fields.keys())
        self._local_cache[key] = all_fields
        return UpgradeResult.success(all_fields)

    def _get_reg_fields(
        self, reg_data: dict[str, Any]
    ) -> UpgradeResult[dict[str, Any], None] | UpgradeResult[None, UpgradeError]:
        key = "fields"
        if key in reg_data:
            item = cast(dict[str, Any], reg_data[key])
            return UpgradeResult.success(item)
        return UpgradeResult.failure(
            UpgradeError(
                "Registry Missing fields configuration",
                "fields",
                "Registry must specify fields configuration for upgrade.",
            ),
            severity=SeverityKind.CRITICAL,
            payload={
                "missing_field": "fields",
                "context": "registry",
            },
        )

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
    ) -> UpgradeResult[FrontMatterMeta, None] | UpgradeResult[None, UpgradeError]: ...
