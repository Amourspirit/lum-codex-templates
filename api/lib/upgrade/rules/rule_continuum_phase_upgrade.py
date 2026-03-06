from typing import Any
from ..exceptions import UpgradeError
from ..types import PhaseInfo
from ..upgrade_result import SeverityKind
from ..upgrade_result import UpgradeResult
from ..protocols.protocol_rules_cache import ProtocolRulesCache
from .rule_upgrade import RuleUpgrade
from src.template.front_mater_meta import FrontMatterMeta
from src.util.result import Result
from ...const import CONTINUUM_DATE_TIME


class RuleContinuumPhaseUpgrade(RuleUpgrade[PhaseInfo]):
    RULE_ORDER = 100
    CONTINUUM_PHASE_FIELD = "continuum_phase"

    def __init__(self, shared_cache: ProtocolRulesCache[PhaseInfo]) -> None:
        super().__init__(shared_cache)
        self._rule_id = "continuum_phase_upgrade"
        self._description = (
            f"Ensures the artifact has a valid {self.CONTINUUM_PHASE_FIELD}."
        )

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
        reg_result = self._get_field_data(reg_data, self.CONTINUUM_PHASE_FIELD)
        if UpgradeResult.is_failure(reg_result):
            return UpgradeResult.failure(reg_result.error)

        field_data = reg_result.data

        allowed_result = self._get_allowed_values(
            field_data, self.CONTINUUM_PHASE_FIELD
        )
        if UpgradeResult.is_failure(allowed_result):
            return UpgradeResult.failure(allowed_result.error)

        allowed = allowed_result.data

        # ---- Determine original state BEFORE modification ----
        had_field = fm_artifact.has_field(self.CONTINUUM_PHASE_FIELD)

        if had_field:
            value = fm_artifact.get_field(self.CONTINUUM_PHASE_FIELD)
            if value not in allowed:
                return UpgradeResult.failure(
                    UpgradeError(
                        f"Invalid {self.CONTINUUM_PHASE_FIELD} '{value}'",
                        self.CONTINUUM_PHASE_FIELD,
                        f"Allowed: {allowed}",
                    ),
                    severity=SeverityKind.ERROR,
                    payload={
                        "value": value,
                        "allowed": list(allowed),
                        "artifact": fm_artifact,
                    },
                )

            # Valid existing value
            self.shared_set(
                "phase_info",
                {
                    "value": value,
                    "allowed": list(allowed),
                    "source": "artifact",
                },
            )

            return UpgradeResult.success(
                fm_artifact,
                payload={
                    f"{self.CONTINUUM_PHASE_FIELD}": value,
                    "source": "artifact",
                    "artifact": fm_artifact,
                },
            )

        date_result = fm_artifact.entry_date
        if Result.is_failure(date_result):
            return UpgradeResult.failure(
                UpgradeError(
                    f"Existing Template is missing or invalid entry_date for default {self.CONTINUUM_PHASE_FIELD} assignment",
                    "entry_date",
                    "Required for default assignment when field is missing",
                ),
                severity=SeverityKind.ERROR,
                payload={
                    "error": str(date_result.error),
                    "artifact": fm_artifact,
                },
            )

        entry_date = date_result.data
        if entry_date < CONTINUUM_DATE_TIME:
            default = "pre"
        else:
            default_result = self._get_default_value(
                field_data, self.CONTINUUM_PHASE_FIELD, allowed
            )
            if UpgradeResult.is_failure(default_result):
                return UpgradeResult.failure(default_result.error)

            default = default_result.data

        # ---- Missing: assign default ----
        fm_artifact.set_field(self.CONTINUUM_PHASE_FIELD, default)

        self.shared_set(
            "phase_info",
            {
                "value": default,
                "allowed": list(allowed),
                "source": "default",
            },
        )

        return UpgradeResult.success(
            fm_artifact,
            severity=SeverityKind.INFO,
            payload={
                f"{self.CONTINUUM_PHASE_FIELD}": default,
                "source": "default_assignment",
                "entry_date": entry_date.isoformat(),
                "artifact": fm_artifact,
            },
        )
