from typing import Any, cast

from src.template.front_mater_meta import FrontMatterMeta
from api.lib.util.result import Result
from ...exceptions import VerifyError, MissingKeyError
from .protocol_verify_rule import ProtocolVerifyRule


class LinkedNodesRule(ProtocolVerifyRule):
    def __init__(self) -> None:
        self._field = "linked_nodes"

    def get_field(self) -> str:
        return self._field

    def _is_numeric_string(self, s: str) -> bool:
        try:
            int(s)
            return True
        except ValueError:
            return False

    def validate(
        self, fm: FrontMatterMeta, registry: dict[str, Any]
    ) -> Result[bool, None] | Result[None, Exception]:

        fields = cast(dict[str, Any], registry.get("fields", {}))
        if self._field not in fields:
            return Result.failure(
                MissingKeyError(
                    f"Missing Key error in field '{self._field}': ",
                    self._field,
                    f"Field '{self._field}' is not defined in the registry.",
                )
            )
        if not fm.has_field(self._field):
            return Result.failure(
                MissingKeyError(
                    f"Missing Key error in field '{self._field}': ",
                    self._field,
                    f"Field '{self._field}' is required but not found in the frontmatter.",
                )
            )
        value = fm.get_field(self._field)
        if not isinstance(value, list):
            return Result.failure(TypeError(f"Field '{self._field}' must be a list."))
        errors: list[str] = []

        for item in value:
            if not isinstance(item, str):
                errors.append(f"Item '{item}' is not a string.")
            else:
                if not self._is_numeric_string(item):
                    errors.append(f"Item '{item}' is not a numeric string.")
        if errors:
            return Result.failure(
                VerifyError(
                    f"Validation errors in field '{self._field}': ",
                    self._field,
                    errors,
                )
            )
        return Result.success(True)
