from typing import Any
from api.lib.protocols import ProtocolRulesCache
from src.template.front_mater_meta import FrontMatterMeta
from ..exceptions import UpgradeError
from ..types import PhaseInfo
from ..upgrade_result import UpgradeResult, SeverityKind
from .rule_upgrade import RuleUpgrade


class RuleTemplateFieldNormalization(RuleUpgrade[PhaseInfo]):
    RULE_ORDER = 110

    def __init__(self, shared_cache: ProtocolRulesCache[PhaseInfo]):
        super().__init__(shared_cache)
        self._rule_id = "template_field_normalization"
        self._description = "Normalize template metadata fields on artifact."

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
        required_fields_result = self._get_reg_required_fields(reg_data)
        if UpgradeResult.is_failure(required_fields_result):
            return UpgradeResult.failure(required_fields_result.error)

        required_fields = required_fields_result.data
        for field in required_fields:
            value = fm_template.get_field(field)
            if value is None:
                return UpgradeResult.failure(
                    UpgradeError(
                        f"Template missing required field '{field}'",
                        field,
                        "Required by template schema",
                    ),
                    severity=SeverityKind.CRITICAL,
                    payload={"template": fm_template},
                )

            fm_artifact.set_field(field, value)

        # Normalize version string (strip leading 'v')
        version = fm_template.template_version
        if isinstance(version, str) and version.startswith("v"):
            fm_artifact.set_field("template_version", version.lstrip("v"))

        return UpgradeResult.success(fm_artifact)
