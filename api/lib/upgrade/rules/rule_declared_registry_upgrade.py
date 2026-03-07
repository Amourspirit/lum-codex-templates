from typing import Any
from src.template.front_mater_meta import FrontMatterMeta
from ..exceptions import UpgradeError
from ..types import PhaseInfo
from ..upgrade_result import UpgradeResult
from ..protocols.protocol_rules_cache import ProtocolRulesCache
from .rule_upgrade import RuleUpgrade


class RuleDeclaredRegistryUpgrade(RuleUpgrade[PhaseInfo]):
    RULE_ORDER = 130

    def __init__(self, shared_cache: ProtocolRulesCache[PhaseInfo]):

        super().__init__(shared_cache)

        self._rule_id = "declared_registry_upgrade"
        self._description = "Normalize declared registry metadata."

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
        reg_data = self._get_registry_data(registry)
        reg_fields_result = self._get_reg_all_fields(reg_data)
        if UpgradeResult.is_failure(reg_fields_result):
            return UpgradeResult.failure(reg_fields_result.error)

        reg_fields = reg_fields_result.data

        for f in reg_fields:
            if fm_template.has_field(f):
                fm_artifact.set_field(f, fm_template.get_field(f))

        return UpgradeResult.success(fm_artifact)
