from typing import Any, cast

from src.template.front_mater_meta import FrontMatterMeta
from api.lib.util.result import Result
from api.lib.exceptions import VerifyError, MissingKeyError
from .protocol_verify_rule import ProtocolVerifyRule


class RuleAllowFields(ProtocolVerifyRule):
    def __init__(self, field: str) -> None:
        self._field = field

    def get_field(self) -> str:
        return self._field

    def validate(
        self, fm: FrontMatterMeta, registry: dict[str, Any]
    ) -> Result[bool, None] | Result[None, Exception]:

        this_field = self.get_field()

        fields = cast(dict[str, Any], registry.get("fields", {}))
        if this_field not in fields:
            return Result.failure(
                MissingKeyError(
                    f"Missing Key error in field '{this_field}': ",
                    this_field,
                    f"Field '{this_field}' is not defined in the registry.",
                )
            )
        if not fm.has_field(this_field):
            return Result.failure(
                MissingKeyError(
                    f"Missing Key error in field '{this_field}': ",
                    this_field,
                    f"Field '{this_field}' is required but not found in the frontmatter.",
                )
            )
        # allowed_values
        if "allowed_values" not in fields[this_field]:
            return Result.failure(
                MissingKeyError(
                    f"Missing Key error in field '{this_field}': ",
                    this_field,
                    f"Missing 'allowed_values' key for field '{this_field}' in the registry.",
                )
            )
        allowed_values = cast(list[str], fields[this_field]["allowed_values"])
        if not isinstance(allowed_values, list):
            return Result.failure(
                VerifyError(
                    f"Validation error in field '{this_field}': ",
                    this_field,
                    f"'allowed_values' for field '{this_field}' must be a list of strings in the registry.",
                )
            )
        allowed_values_set = set(allowed_values)

        value = fm.get_field(this_field)
        if not isinstance(value, str):
            return Result.failure(TypeError(f"Field '{this_field}' must be a string."))

        if value not in allowed_values_set:
            return Result.failure(
                VerifyError(
                    f"Validation error in field '{this_field}': ",
                    this_field,
                    f"Value '{value}' is not an allowed value for field '{this_field}'. Allowed values are: {', '.join(allowed_values)}.",
                )
            )

        return Result.success(True)
