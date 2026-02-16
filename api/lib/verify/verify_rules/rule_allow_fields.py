from typing import Any, Literal, cast

from src.template.front_mater_meta import FrontMatterMeta
from api.lib.util.result import Result
from api.lib.exceptions import VerifyError, MissingKeyError, RequiredFieldMissingError
from .protocol_verify_rule import ProtocolVerifyRule


class RuleAllowFields(ProtocolVerifyRule):
    def __init__(self, field: str, match_kind: Literal["any", "all"] = "all") -> None:
        self._field = field
        self._match_kind = match_kind

    def get_field(self) -> str:
        return self._field

    def _validate_allowed_str(
        self, value: Any, allowed_values_set: set
    ) -> Result[bool, None] | Result[None, Exception]:
        if value not in allowed_values_set:
            allowed_values = sorted(allowed_values_set)
            return Result.failure(
                VerifyError(
                    f"Validation error in field '{self._field}': ",
                    self._field,
                    f"Value '{value}' is not an allowed value for field '{self._field}'. Allowed values are: {', '.join(allowed_values)}.",
                )
            )

        return Result.success(True)

    def _validate_allowed_list_any(
        self, value: list[str], allowed_values_set: set
    ) -> Result[bool, None] | Result[None, Exception]:
        # All Values in allowed_values_set must be present in the value list
        for item in value:
            if item not in allowed_values_set:
                allowed_values = sorted(allowed_values_set)
                return Result.failure(
                    VerifyError(
                        f"Validation error in field '{self._field}': ",
                        self._field,
                        f"Value '{item}' is not an allowed value for field '{self._field}'. Allowed values are: {', '.join(allowed_values)}.",
                    )
                )
        # At least one value in the value list must be present in the allowed_values_set
        if not any(item in allowed_values_set for item in value):
            allowed_values = sorted(allowed_values_set)
            return Result.failure(
                VerifyError(
                    f"Validation error in field '{self._field}': ",
                    self._field,
                    f"At least one value in the list must be an allowed value for field '{self._field}'. Allowed values are: {', '.join(allowed_values)}.",
                )
            )
        return Result.success(True)

    def _validate_allowed_list_all(
        self, value: list[str], allowed_values_set: set
    ) -> Result[bool, None] | Result[None, Exception]:
        # All Values in the value list must be present in the allowed_values_set and vise versa
        value_set = set(value)
        if value_set != allowed_values_set:
            allowed_values = sorted(allowed_values_set)
            return Result.failure(
                VerifyError(
                    f"Validation error in field '{self._field}': ",
                    self._field,
                    f"All values in the list must be allowed values for field '{self._field}' and all allowed values must be present in the list. Allowed values are: {', '.join(allowed_values)}.",
                )
            )

        return Result.success(True)

    def validate(
        self, fm: FrontMatterMeta, registry: dict[str, Any]
    ) -> Result[bool, None] | Result[None, Exception]:

        fields = cast(dict[str, Any], registry.get("fields", {}))
        field_data = fields.get(self._field, {})
        if not field_data:
            return Result.failure(
                VerifyError(
                    f"No field data found in registry '{self._field}': ",
                    self._field,
                    f"Field '{self._field}' is not defined in the registry.",
                )
            )

        if self._field not in fields:
            return Result.failure(
                MissingKeyError(
                    f"Missing Key error in field '{self._field}': ",
                    self._field,
                    f"Field '{self._field}' is not defined in the registry.",
                )
            )

        field_required = field_data.get("required", False)

        if field_required and not fm.has_field(self._field):
            return Result.failure(
                RequiredFieldMissingError(
                    f"Required field '{self._field}' is missing: ",
                    self._field,
                    f"Field '{self._field}' is required but not found in the frontmatter.",
                )
            )

        if "allowed_values" not in fields[self._field]:
            return Result.failure(
                MissingKeyError(
                    f"Missing Key error in field '{self._field}': ",
                    self._field,
                    f"Missing 'allowed_values' key for field '{self._field}' in the registry.",
                )
            )

        allowed_values = cast(list[str], fields[self._field]["allowed_values"])

        if not isinstance(allowed_values, list):
            return Result.failure(
                VerifyError(
                    f"Validation error in field '{self._field}': ",
                    self._field,
                    f"'allowed_values' for field '{self._field}' must be a list of strings in the registry.",
                )
            )
        allowed_values_set = set(allowed_values)

        value = fm.get_field(self._field)
        if isinstance(value, str):
            if not value:
                return Result.failure(
                    VerifyError(
                        f"Validation error in field '{self._field}': ",
                        self._field,
                        f"Value for field '{self._field}' cannot be an empty string.",
                    )
                )
            return self._validate_allowed_str(value, allowed_values_set)
        elif isinstance(value, list) and all(isinstance(item, str) for item in value):
            if not value:
                return Result.failure(
                    VerifyError(
                        f"Validation error in field '{self._field}': ",
                        self._field,
                        f"Value list for field '{self._field}' cannot be empty.",
                    )
                )

            if self._match_kind == "any":
                return self._validate_allowed_list_any(value, allowed_values_set)
            else:
                return self._validate_allowed_list_all(value, allowed_values_set)
        else:
            return Result.failure(
                VerifyError(
                    f"Validation error in field '{self._field}': ",
                    self._field,
                    f"Value for field '{self._field}' must be either a string or a list of strings.",
                )
            )
