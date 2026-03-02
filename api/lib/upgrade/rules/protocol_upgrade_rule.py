from typing import Any
from typing import Protocol
from api.lib.util.result import Result
from src.template.front_mater_meta import FrontMatterMeta


class ProtocolUpgradeRule(Protocol):
    def get_rule_id(self) -> str: ...
    def get_description(self) -> str: ...
    def get_order(self) -> int: ...
    def should_run(self, fm_artifact, fm_template, registry) -> bool: ...
    def apply(
        self,
        fm_artifact: FrontMatterMeta,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> Result[FrontMatterMeta, None] | Result[None, Exception]: ...
