from typing import Any, Protocol, ClassVar, runtime_checkable
from src.template.front_mater_meta import FrontMatterMeta
from ..upgrade_result import UpgradeResult as UpgradeResult
from ..exceptions import UpgradeError


@runtime_checkable
class ProtocolUpgradeRule(Protocol):
    RULE_ORDER: ClassVar[int]

    def get_rule_id(self) -> str: ...
    def get_description(self) -> str: ...
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
    ) -> UpgradeResult[FrontMatterMeta, None] | UpgradeResult[None, UpgradeError]: ...

    @property
    def rule_name(self) -> str: ...


class UpgradeRuleFactory(Protocol):
    """Protocol for class constructors."""

    def __call__(self) -> ProtocolUpgradeRule: ...
