from typing import Any
from typing import Protocol
from api.lib.util.result import Result
from src.template.front_mater_meta import FrontMatterMeta


class ProtocolVerifyRule(Protocol):
    def get_field(self) -> str: ...
    def validate(
        self, fm: FrontMatterMeta, registry: dict[str, Any]
    ) -> Result[bool, None] | Result[None, Exception]: ...
