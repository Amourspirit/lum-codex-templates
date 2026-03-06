from typing import Any
from src.template.front_mater_meta import FrontMatterMeta
from ..exceptions import UpgradeError
from ..protocols.protocol_rules_cache import ProtocolRulesCache
from ..types import PhaseInfo
from ..upgrade_result import UpgradeResult
from .rule_upgrade import RuleUpgrade


class RuleContentCleanup(RuleUpgrade[PhaseInfo]):
    RULE_ORDER = 100

    def __init__(self, shared_cache: ProtocolRulesCache[PhaseInfo]):
        super().__init__(shared_cache)
        self._rule_id = "content_cleanup"
        self._description = "Normalize and clean artifact content."

    def get_rule_id(self):
        return self._rule_id

    def get_description(self):
        return self._description

    def should_run(
        self,
        fm_artifact: FrontMatterMeta,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> bool:
        return True

    def apply(
        self,
        fm_artifact: FrontMatterMeta,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> UpgradeResult[FrontMatterMeta, None] | UpgradeResult[None, UpgradeError]:

        lines = fm_artifact.content.splitlines()
        cleaned = [
            "* * *" if line.strip() == "---" else line.rstrip() for line in lines
        ]

        fm_artifact.content = "\n".join(cleaned)
        return UpgradeResult.success(fm_artifact)
