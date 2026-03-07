from typing import Any
from src.template.front_mater_meta import FrontMatterMeta
from ..exceptions import UpgradeError
from ..protocols.protocol_rules_cache import ProtocolRulesCache
from ..types import PhaseInfo
from ..upgrade_result import UpgradeResult
from .rule_upgrade import RuleUpgrade

OBSOLETE_FIELD_SAFEKEEP = {
    "artifact_id",
    "artifact_name",
    "registry_id",
    "codex_entry",
    "continuum_phase",
}


class RuleRemoveObsoleteFields(RuleUpgrade[PhaseInfo]):
    RULE_ORDER = 140

    def __init__(self, shared_cache: ProtocolRulesCache[PhaseInfo]):
        super().__init__(shared_cache)
        self._rule_id = "remove_obsolete_fields"
        self._description = "Remove frontmatter fields not present in template."

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

        template_keys = set(fm_template.get_keys())
        artifact_keys = set(fm_artifact.get_keys())
        remove_keys = artifact_keys - template_keys - OBSOLETE_FIELD_SAFEKEEP

        for k in remove_keys:
            fm_artifact.remove_field(k)

        return UpgradeResult.success(
            fm_artifact, payload={"removed_fields": sorted(remove_keys)}
        )
