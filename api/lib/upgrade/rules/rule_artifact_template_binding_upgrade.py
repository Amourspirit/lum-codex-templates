from typing import Any
from src.template.front_mater_meta import FrontMatterMeta
from api.lib.protocols import ProtocolRulesCache
from ..exceptions import UpgradeError
from ..types import PhaseInfo
from ..upgrade_result import UpgradeResult
from .rule_upgrade import RuleUpgrade


class RuleArtifactTemplateBindingUpgrade(RuleUpgrade[PhaseInfo]):
    RULE_ORDER = 120

    def __init__(self, shared_cache: ProtocolRulesCache[PhaseInfo]):
        super().__init__(shared_cache)
        self._rule_id = "artifact_template_binding"
        self._description = "Ensure artifact references correct template."

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

        artifact_tid = fm_artifact.template_id
        new_tid = fm_template.template_id

        if artifact_tid != new_tid:
            fm_artifact.template_id = new_tid

        return UpgradeResult.success(fm_artifact)
