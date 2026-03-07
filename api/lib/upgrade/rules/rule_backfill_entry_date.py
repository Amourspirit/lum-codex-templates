from typing import Any
from datetime import datetime
from src.template.front_mater_meta import FrontMatterMeta
from ..exceptions import UpgradeError
from ..protocols.protocol_rules_cache import ProtocolRulesCache
from ..types import PhaseInfo
from ..upgrade_result import UpgradeResult
from .rule_upgrade import RuleUpgrade


class RuleBackfillEntryDate(RuleUpgrade[PhaseInfo]):
    RULE_ORDER = 100

    def __init__(self, shared_cache: ProtocolRulesCache[PhaseInfo]):
        super().__init__(shared_cache)
        self._rule_id = "entry_date_backfill"
        self._description = "Backfill missing entry_date with filesystem timestamp."

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

        result = fm_artifact.entry_date
        if not result.result_is_failure():
            return UpgradeResult.success(fm_artifact)

        # fallback
        ts = datetime.now().isoformat()
        fm_artifact.set_field("entry_date", ts)

        return UpgradeResult.success(fm_artifact, payload={"assigned": ts})
