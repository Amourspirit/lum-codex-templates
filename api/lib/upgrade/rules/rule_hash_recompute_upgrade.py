from typing import Any
from api.lib.protocols import ProtocolRulesCache
from src.template.front_mater_meta import FrontMatterMeta
from ..exceptions import UpgradeError
from ..types import PhaseInfo
from ..upgrade_result import UpgradeResult
from .rule_upgrade import RuleUpgrade


class RuleHashRecomputeUpgrade(RuleUpgrade[PhaseInfo]):
    RULE_ORDER = 900

    def __init__(self, shared_cache: ProtocolRulesCache[PhaseInfo]):
        super().__init__(shared_cache)
        self._rule_id = "hash_recompute"
        self._description = "Recompute SHA256 hash after upgrade."

    def should_run(
        self,
        fm_artifact: FrontMatterMeta,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> bool:
        return True

    def get_rule_id(self) -> str:
        return self._rule_id

    def get_description(self) -> str:
        return self._description

    def apply(
        self,
        fm_artifact: FrontMatterMeta,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> UpgradeResult[FrontMatterMeta, None] | UpgradeResult[None, UpgradeError]:

        fm_artifact.recompute_sha256()
        return UpgradeResult.success(fm_artifact)
