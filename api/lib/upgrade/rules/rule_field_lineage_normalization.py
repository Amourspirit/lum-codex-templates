from typing import Any
from api.lib.protocols import ProtocolRulesCache
from src.template.front_mater_meta import FrontMatterMeta
from ..exceptions import UpgradeError
from ..types import PhaseInfo
from ..upgrade_result import UpgradeResult
from .rule_upgrade import RuleUpgrade


LINEAGE_MIGRATIONS = {
    "stone_name": "artifact_name",
    "glyph_type": "artifact_type",
    "glyph_status": "artifact_status",
    "glyph_epithet": "artifact_epithet",
}


class RuleFieldLineageNormalization(RuleUpgrade[PhaseInfo]):
    # Handles deprecated → new field names.
    RULE_ORDER = 150

    def __init__(self, shared_cache: ProtocolRulesCache[PhaseInfo]):
        super().__init__(shared_cache)

        self._rule_id = "field_lineage_normalization"
        self._description = "Migrate deprecated metadata fields."

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

        for old, new in LINEAGE_MIGRATIONS.items():
            if fm_artifact.has_field(old):
                fm_artifact.set_field(new, fm_artifact.get_field(old))
                fm_artifact.remove_field(old)

        return UpgradeResult.success(fm_artifact)
