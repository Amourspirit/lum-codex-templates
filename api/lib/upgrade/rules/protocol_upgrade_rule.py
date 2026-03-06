from typing import Any, Generic, Protocol, TypeVar, runtime_checkable
from src.template.front_mater_meta import FrontMatterMeta
from ..upgrade_result import UpgradeResult as Result
from ..exceptions import UpgradeError
from .protocol_rules_cache import ProtocolRulesCache

C = TypeVar("C")  # Cache type variable


@runtime_checkable
class ProtocolUpgradeRule(Protocol, Generic[C]):
    def get_rule_id(self) -> str: ...
    def get_description(self) -> str: ...
    def get_order(self) -> int: ...
    def should_run(
        self,
        fm_artifact: FrontMatterMeta,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> bool: ...
    def shared_set(self, key: str, value: C) -> None: ...
    def shared_get(self, key: str, default: C | None = None) -> Any: ...
    def apply(
        self,
        fm_artifact: FrontMatterMeta,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> Result[FrontMatterMeta, None] | Result[None, UpgradeError]: ...
    @property
    def shared_cache(self) -> ProtocolRulesCache[C]: ...
    @property
    def rule_name(self) -> str: ...


class UpgradeRuleFactory(Protocol, Generic[C]):
    """Protocol for rule class constructors."""

    def __call__(
        self, shared_cache: ProtocolRulesCache[C]
    ) -> ProtocolUpgradeRule[C]: ...
