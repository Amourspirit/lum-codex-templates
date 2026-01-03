from typing import Any
from typing import Protocol
from ....util.result import Result


class ProtocolVerifyRule(Protocol):
    def get_field_name(self) -> str: ...
    def validate(self, value: Any) -> Result[bool, None] | Result[None, Exception]: ...
