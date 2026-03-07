from typing import Any, Generic, cast, Literal, TypeVar
from api.lib.protocols.protocol_rules_cache import ProtocolRulesCache
from src.template.front_mater_meta import FrontMatterMeta
from src.util.severity_kind import SeverityKind
from ..verify_result import VerifyResult
from ..exceptions import VerifyError, MissingKeyError, RequiredFieldMissingError
from .rule_verify import RuleVerify

T = TypeVar("T")


class RuleAllowFields(RuleVerify[T], Generic[T]):
    RULE_ORDER = 100

    def __init__(
        self,
        shared_cache: ProtocolRulesCache[T],
        field: str,
        match_kind: Literal["any", "all"] = "all",
    ) -> None:
        super().__init__(shared_cache)
        self._field = field
        self._match_kind = match_kind
        self._desc = f"Validate that field '{self._field}' only contains allowed values as defined in the registry. Match kind: {self._match_kind}."

    def get_rule_id(self) -> str:
        return self._field

    def get_description(self) -> str:
        return self._desc

    def should_run(
        self,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> bool:
        return True

    def _validate_allowed_str(
        self, fm_template: FrontMatterMeta, value: Any, allowed_values_set: set
    ) -> VerifyResult[FrontMatterMeta, None] | VerifyResult[None, VerifyError]:
        if value not in allowed_values_set:
            allowed_values = sorted(allowed_values_set)
            return VerifyResult.failure(
                VerifyError(
                    f"Validation error in field '{self._field}': ",
                    self._field,
                    f"Value '{value}' is not an allowed value for field '{self._field}'. Allowed values are: {', '.join(allowed_values)}.",
                )
            )

        return VerifyResult.success(fm_template)

    def _validate_allowed_list_any(
        self, fm_template: FrontMatterMeta, value: list[str], allowed_values_set: set
    ) -> VerifyResult[FrontMatterMeta, None] | VerifyResult[None, VerifyError]:
        # All Values in allowed_values_set must be present in the value list
        for item in value:
            if item not in allowed_values_set:
                allowed_values = sorted(allowed_values_set)
                return VerifyResult.failure(
                    VerifyError(
                        f"Validation error in field '{self._field}': ",
                        self._field,
                        f"Value '{item}' is not an allowed value for field '{self._field}'. Allowed values are: {', '.join(allowed_values)}.",
                    ),
                    severity=SeverityKind.ERROR,
                    payload={"field": self._field},
                )
        # At least one value in the value list must be present in the allowed_values_set
        if not any(item in allowed_values_set for item in value):
            allowed_values = sorted(allowed_values_set)
            return VerifyResult.failure(
                VerifyError(
                    f"Validation error in field '{self._field}': ",
                    self._field,
                    f"At least one value in the list must be an allowed value for field '{self._field}'. Allowed values are: {', '.join(allowed_values)}.",
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self._field},
            )
        return VerifyResult.success(fm_template)

    def _validate_allowed_list_all(
        self, fm_template: FrontMatterMeta, value: list[str], allowed_values_set: set
    ) -> VerifyResult[FrontMatterMeta, None] | VerifyResult[None, VerifyError]:
        # All Values in the value list must be present in the allowed_values_set and vise versa
        value_set = set(value)
        if value_set != allowed_values_set:
            allowed_values = sorted(allowed_values_set)
            return VerifyResult.failure(
                VerifyError(
                    f"Validation error in field '{self._field}': ",
                    self._field,
                    f"All values in the list must be allowed values for field '{self._field}' and all allowed values must be present in the list. Allowed values are: {', '.join(allowed_values)}.",
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self._field},
            )

        return VerifyResult.success(fm_template)

    def apply(
        self,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> VerifyResult[FrontMatterMeta, None] | VerifyResult[None, VerifyError]:

        fields = cast(dict[str, Any], registry.get("fields", {}))
        field_data = fields.get(self._field, {})
        if not field_data:
            return VerifyResult.failure(
                VerifyError(
                    f"No field data found in registry '{self._field}': ",
                    self._field,
                    f"Field '{self._field}' is not defined in the registry.",
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self._field},
            )

        if self._field not in fields:
            return VerifyResult.failure(
                MissingKeyError(
                    f"Missing Key error in field '{self._field}': ",
                    self._field,
                    f"Field '{self._field}' is not defined in the registry.",
                ),
                severity=SeverityKind.WARNING,
                payload={"field": self._field},
            )

        field_required = field_data.get("required", False)

        if field_required and not fm_template.has_field(self._field):
            return VerifyResult.failure(
                RequiredFieldMissingError(
                    f"Required field '{self._field}' is missing: ",
                    self._field,
                    f"Field '{self._field}' is required but not found in the frontmatter.",
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self._field},
            )

        if "allowed_values" not in fields[self._field]:
            return VerifyResult.failure(
                MissingKeyError(
                    f"Missing Key error in field '{self._field}': ",
                    self._field,
                    f"Missing 'allowed_values' key for field '{self._field}' in the registry.",
                ),
                severity=SeverityKind.WARNING,
                payload={"field": self._field},
            )

        allowed_values = cast(list[str], fields[self._field]["allowed_values"])

        if not isinstance(allowed_values, list):
            return VerifyResult.failure(
                VerifyError(
                    f"Validation error in field '{self._field}': ",
                    self._field,
                    f"'allowed_values' for field '{self._field}' must be a list of strings in the registry.",
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self._field},
            )
        allowed_values_set = set(allowed_values)

        value = fm_template.get_field(self._field)
        if isinstance(value, str):
            if not value:
                return VerifyResult.failure(
                    VerifyError(
                        f"Validation error in field '{self._field}': ",
                        self._field,
                        f"Value for field '{self._field}' cannot be an empty string.",
                    ),
                    severity=SeverityKind.ERROR,
                    payload={"field": self._field},
                )
            return self._validate_allowed_str(fm_template, value, allowed_values_set)
        elif isinstance(value, list) and all(isinstance(item, str) for item in value):
            if not value:
                return VerifyResult.failure(
                    VerifyError(
                        f"Validation error in field '{self._field}': ",
                        self._field,
                        f"Value list for field '{self._field}' cannot be empty.",
                    ),
                    severity=SeverityKind.ERROR,
                    payload={"field": self._field},
                )

            if self._match_kind == "any":
                return self._validate_allowed_list_any(
                    fm_template, value, allowed_values_set
                )
            else:
                return self._validate_allowed_list_all(
                    fm_template, value, allowed_values_set
                )
        else:
            return VerifyResult.failure(
                VerifyError(
                    f"Validation error in field '{self._field}': ",
                    self._field,
                    f"Value for field '{self._field}' must be either a string or a list of strings.",
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self._field},
            )
