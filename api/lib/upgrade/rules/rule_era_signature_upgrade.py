from typing import Any
from src.template.front_mater_meta import FrontMatterMeta
from ..exceptions import UpgradeError
from ..types import PhaseInfo
from ..upgrade_result import UpgradeResult
from ..protocols.protocol_rules_cache import ProtocolRulesCache
from .rule_upgrade import RuleUpgrade


ERA_SIGNATURE_FIELDS = [
    "era_signature_sovereignty_class",
    "era_signature_continuum_frame",
    "era_signature_harmonic_pulse",
    "era_signature_field_resonance",
]


class RuleEraSignatureUpgrade(RuleUpgrade[PhaseInfo]):
    RULE_ORDER = 100

    def __init__(self, shared_cache: ProtocolRulesCache[PhaseInfo]) -> None:
        super().__init__(shared_cache)

        self._rule_id = "era_signature_upgrade"
        self._description = "Backfill era-signature metadata using registry defaults."

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

        reg_data = self._get_registry_data(registry)
        fields_result = self._get_reg_fields(reg_data)
        if UpgradeResult.is_failure(fields_result):
            return UpgradeResult.failure(fields_result.error)
        field_data = fields_result.data

        for field in ERA_SIGNATURE_FIELDS:
            if fm_artifact.has_field(field):
                continue

            if field not in field_data:
                continue  # not required

            default_result = self._get_default_value(field_data, field)
            if UpgradeResult.is_success(default_result):
                fm_artifact.set_field(field, default_result.data)

        return UpgradeResult.success(fm_artifact)
