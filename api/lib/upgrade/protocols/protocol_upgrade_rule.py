from typing import Any, Protocol, runtime_checkable
from src.template.front_mater_meta import FrontMatterMeta
from ..upgrade_result import UpgradeResult as Result
from ..exceptions import UpgradeError


@runtime_checkable
class ProtocolUpgradeRule(Protocol):
    def get_rule_id(self) -> str: ...
    def get_description(self) -> str: ...
    def get_order(self) -> int: ...
    def should_run(
        self,
        fm_artifact: FrontMatterMeta,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> bool: ...
    def apply(
        self,
        fm_artifact: FrontMatterMeta,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> Result[FrontMatterMeta, None] | Result[None, UpgradeError]: ...

    @property
    def rule_name(self) -> str: ...


class UpgradeRuleFactory(Protocol):
    """Protocol for class constructors."""

    def __call__(self) -> ProtocolUpgradeRule: ...
