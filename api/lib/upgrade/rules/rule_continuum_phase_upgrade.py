from typing import Any, cast
from ..exceptions import MissingKeyError, UpgradeError
from ..types import PhaseInfo
from ..upgrade_result import SeverityKind
from ..upgrade_result import UpgradeResult as Result
from ..protocols.protocol_rules_cache import ProtocolRulesCache
from .rule_upgrade import RuleUpgrade
from src.template.front_mater_meta import FrontMatterMeta


class RuleContinuumPhaseUpgrade(RuleUpgrade[PhaseInfo]):
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

    def get_order(self) -> int:
        return 100  # default

    def should_run(self, fm_artifact, fm_template, registry) -> bool:
        return True

    def apply(
        self,
        fm_artifact: FrontMatterMeta,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> Result[FrontMatterMeta, None] | Result[None, UpgradeError]:

        reg_data = self._get_registry_data(registry)
        reg_cpf: dict[str, Any] | None = reg_data.get(self.CONTINUUM_PHASE_FIELD, None)

        if reg_cpf is None:
            return Result.failure(
                MissingKeyError(
                    f"Registry Missing {self.CONTINUUM_PHASE_FIELD} configuration",
                    self.CONTINUUM_PHASE_FIELD,
                    f"Registry must specify {self.CONTINUUM_PHASE_FIELD} configuration for upgrade.",
                ),
                severity=SeverityKind.CRITICAL,
                payload={
                    "missing_field": self.CONTINUUM_PHASE_FIELD,
                    "context": "registry",
                },
            )
        allowed = set(reg_cpf.get("allowed_values", []))
        if len(allowed) == 0:
            return Result.failure(
                MissingKeyError(
                    f"Registry Missing allowed_values for {self.CONTINUUM_PHASE_FIELD}",
                    self.CONTINUUM_PHASE_FIELD,
                    f"Registry must specify allowed values for {self.CONTINUUM_PHASE_FIELD}.",
                ),
                severity=SeverityKind.CRITICAL,
                payload={
                    "field": self.CONTINUUM_PHASE_FIELD,
                    "issue": "no_allowed_values",
                },
            )

        default = cast(str | None, reg_cpf.get("default_value", None))

        if default not in allowed:
            return Result.failure(
                UpgradeError(
                    f"Default {self.CONTINUUM_PHASE_FIELD} '{default}' not allowed by registry",
                    self.CONTINUUM_PHASE_FIELD,
                    f"Allowed values: {allowed}",
                ),
                severity=SeverityKind.CRITICAL,
                payload={
                    "default_value": default,
                    "allowed_values": list(allowed),
                    "context": "invalid_registry_default",
                },
            )

        # ---- Determine original state BEFORE modification ----
        had_field = fm_artifact.has_field(self.CONTINUUM_PHASE_FIELD)

        if had_field:
            value = fm_artifact.get_field(self.CONTINUUM_PHASE_FIELD)
            if value not in allowed:
                return Result.failure(
                    UpgradeError(
                        f"Invalid {self.CONTINUUM_PHASE_FIELD} '{value}'",
                        self.CONTINUUM_PHASE_FIELD,
                        f"Allowed: {allowed}",
                    ),
                    severity=SeverityKind.ERROR,
                    payload={"value": value, "allowed": list(allowed)},
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

            return Result.success(
                fm_artifact,
                payload={f"{self.CONTINUUM_PHASE_FIELD}": value, "source": "artifact"},
            )

        if default is None:
            return Result.failure(
                UpgradeError(
                    f"{self.CONTINUUM_PHASE_FIELD} missing and no default provided",
                    self.CONTINUUM_PHASE_FIELD,
                    f"the default_value is missing. Allowed values: {allowed}",
                ),
                severity=SeverityKind.ERROR,
                payload={
                    "allowed_values": list(allowed),
                    "context": "missing_field_no_default",
                },
            )

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

        return Result.success(
            fm_artifact,
            severity=SeverityKind.INFO,
            payload={
                f"{self.CONTINUUM_PHASE_FIELD}": default,
                "source": "default_assignment",
            },
        )
