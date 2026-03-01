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
