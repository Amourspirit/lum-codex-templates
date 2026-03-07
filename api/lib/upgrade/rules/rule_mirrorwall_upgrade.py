from typing import Any
from api.lib.protocols import ProtocolRulesCache
from src.template.front_mater_meta import FrontMatterMeta
from ..exceptions import UpgradeError
from ..types import PhaseInfo
from ..upgrade_result import UpgradeResult
from .rule_upgrade import RuleUpgrade


class RuleMirrorwallUpgrade(RuleUpgrade[PhaseInfo]):
    RULE_ORDER = 180

    def __init__(self, shared_cache: ProtocolRulesCache[PhaseInfo]):
        super().__init__(shared_cache)
        self._rule_id = "mirrorwall_upgrade"
        self._description = "Normalize mirrorwall metadata."

    def get_rule_id(self) -> str:
        return self._rule_id

    def get_description(self) -> str:
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

        if not fm_artifact.has_field("mirrorwall_status"):
            fm_artifact.set_field("mirrorwall_status", "pending")

        if not fm_artifact.has_field("mirror_chamber"):
            fm_artifact.set_field("mirror_chamber", "Nahema'el")

        return UpgradeResult.success(fm_artifact)
