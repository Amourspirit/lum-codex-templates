from typing import Any
from ...util.result import Result
from ...exceptions.verify_error import VerifyError
from .protocol_verify_rule import ProtocolVerifyRule


class LinkedNodesRule(ProtocolVerifyRule):
    def __init__(self) -> None:
        self._field_name = "linked_nodes"

    def get_field_name(self) -> str:
        return self._field_name

    def _is_numeric_string(self, s: str) -> bool:
        try:
            int(s)
            return True
        except ValueError:
            return False

    def validate(self, value: Any) -> Result[bool, None] | Result[None, Exception]:
        if not isinstance(value, list):
            return Result.failure(
                TypeError(f"Field '{self._field_name}' must be a list.")
            )
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
                    f"Validation errors in field '{self._field_name}': ",
                    self._field_name,
                    errors,
                )
            )
        return Result.success(True)
