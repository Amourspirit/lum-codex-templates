from typing import Any, cast

from src.template.front_mater_meta import FrontMatterMeta
from api.lib.util.result import Result
from api.lib.exceptions import (
    VerifyError,
    MissingKeyError,
    RequiredFieldMissingError,
    NullFieldError,
)
from .protocol_verify_rule import ProtocolVerifyRule


class RuleBoolean(ProtocolVerifyRule):
    def __init__(self, field: str) -> None:
        self._field = field

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

        field_nullable = field_data.get("nullable", False)

        value = fm.get_field(self._field)
        if value is None:
            if field_nullable:
                return Result.success(True)
            else:
                return Result.failure(
                    NullFieldError(
                        f"Null field error in field '{self._field}': ",
                        self._field,
                        f"Field '{self._field}' cannot be null.",
                    )
                )

        if not isinstance(value, bool):
            return Result.failure(
                VerifyError(
                    f"Validation error in field '{self._field}': ",
                    self._field,
                    f"Value for field '{self._field}' must be a boolean",
                )
            )
        return Result.success(True)
