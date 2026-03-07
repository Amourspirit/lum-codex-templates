from typing import Any, Protocol, ClassVar, runtime_checkable
from src.template.front_mater_meta import FrontMatterMeta
from ..verify_result import VerifyResult
from ..exceptions import VerifyError


@runtime_checkable
class ProtocolVerifyRule(Protocol):
    RULE_ORDER: ClassVar[int]

    def get_rule_id(self) -> str: ...
    def get_description(self) -> str: ...
    def should_run(
        self,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> bool: ...
    def apply(
        self,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> VerifyResult[FrontMatterMeta, None] | VerifyResult[None, VerifyError]: ...

    @property
    def rule_name(self) -> str: ...


class VerifyRuleFactory(Protocol):
    """Protocol for class constructors."""

    def __call__(self) -> ProtocolVerifyRule: ...
