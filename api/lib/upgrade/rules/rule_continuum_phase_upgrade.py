from typing import Any
from src.util.result import Result, SeverityKind
from src.template.front_mater_meta import FrontMatterMeta
from .protocol_upgrade_rule import ProtocolUpgradeRule
from .rule_upgrade import RuleUpgrade
from ..exceptions import MissingKeyError, UpgradeError


class RuleContinuumPhaseUpgrade(RuleUpgrade, ProtocolUpgradeRule):
    CONTINUUM_PHASE_FIELD = "continuum_phase"

    def __init__(self) -> None:
        self._rule_id = "continuum_phase_upgrade"
        self._description = "Ensures the artifact has a valid continuum_phase."
        self._cache = {}

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
    ) -> Result[FrontMatterMeta, None] | Result[None, Exception]:
        reg_data = self._get_registry_data(registry)
        reg_cpf: dict[str, Any] | None = reg_data.get(self.CONTINUUM_PHASE_FIELD, None)
        if reg_cpf is None:
            return Result.failure(
                MissingKeyError(
                    f"Registry Missing {self.CONTINUUM_PHASE_FIELD} configuration",
                    self.CONTINUUM_PHASE_FIELD,
                    f"Registry must specify {self.CONTINUUM_PHASE_FIELD} configuration for upgrade.",
                ),
                severity=SeverityKind.ERROR,
            )
        allowed_cpf = set(reg_cpf.get("allowed_values", []))
        if len(allowed_cpf) == 0:
            return Result.failure(
                MissingKeyError(
                    f"Registry Missing allowed_values for {self.CONTINUUM_PHASE_FIELD}",
                    self.CONTINUUM_PHASE_FIELD,
                    f"Registry must specify allowed values for {self.CONTINUUM_PHASE_FIELD}.",
                ),
                severity=SeverityKind.ERROR,
            )

        default_cpf = reg_cpf.get("default_value", "post")
        if fm_artifact.has_field(self.CONTINUUM_PHASE_FIELD):
            value = fm_artifact.get_field(self.CONTINUUM_PHASE_FIELD)
            if value not in allowed_cpf:
                return Result.failure(
                    UpgradeError(
                        f"Invalid continuum_phase value '{value}'",
                        self.CONTINUUM_PHASE_FIELD,
                        f"Allowed values: {allowed_cpf}",
                    ),
                    severity=SeverityKind.ERROR,
                )
        else:
            fm_artifact.set_field(self.CONTINUUM_PHASE_FIELD, default_cpf)
        return Result.success(fm_artifact, severity=SeverityKind.INFO)
