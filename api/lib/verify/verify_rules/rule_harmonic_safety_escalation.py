from typing import Any
from src.template.front_mater_meta import FrontMatterMeta
from api.lib.protocols.protocol_rules_cache import ProtocolRulesCache
from src.util.severity_kind import SeverityKind
from ..verify_result import VerifyResult
from ..exceptions import (
    VerifyError,
    MissingKeyError,
    SafetyAbortError,
    SafetyRestrictionError,
    SafetyWarningError,
)
from .rule_verify import RuleVerify
from .types import PhaseInfo


class RuleHarmonicSafetyEscalation(RuleVerify[PhaseInfo]):
    """
    Harmonic Safety Validation + Escalation Logic

    Computes escalation tier from:
      - harmonic_safety_dreamline_instability  (bool)
      - harmonic_safety_mirrorwall_feedback_risk (enum)
      - harmonic_safety_arc_pressure (enum)

    Applies architectural restrictions on rendering and invocation safety.
    """

    RULE_ORDER = 100
    DREAMLINE_FIELD = "harmonic_safety_dreamline_instability"
    FEEDBACK_FIELD = "harmonic_safety_mirrorwall_feedback_risk"
    ARC_FIELD = "harmonic_safety_arc_pressure"

    def __init__(self, shared_cache: ProtocolRulesCache[PhaseInfo]) -> None:
        super().__init__(shared_cache)
        self._field = self.DREAMLINE_FIELD
        self._desc = "Validate harmonic safety fields and apply escalation rules based on registry values."

    def get_rule_id(self) -> str:
        return self._field

    def get_description(self) -> str:
        return self._desc

    def should_run(
        self,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> bool:
        return True

    # ----------------------------------------------------
    # ESCALATION COMPUTATION
    # ----------------------------------------------------
    def _compute_escalation_tier(
        self,
        dreamline: bool,
        feedback: str,
        arc: str,
    ) -> int:
        """
        Returns escalation tier (0-3)
        """

        # Tier 3 — Critical
        if arc == "severe":
            return 3

        # Tier 2 — Restricted
        if dreamline or feedback == "high" or arc == "moderate":
            return 2

        # Tier 1 — Caution
        if feedback == "medium" or arc == "minor":
            return 1

        # Tier 0 — Safe
        return 0

    # ----------------------------------------------------
    # FULL VALIDATION (BASE + ESCALATION)
    # ----------------------------------------------------
    def apply(
        self,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> VerifyResult[FrontMatterMeta, None] | VerifyResult[None, VerifyError]:

        reg_data = registry.get("metadata", registry)

        # Backward compatibility: if none present, report missing (warning)
        missing_all = (
            self.DREAMLINE_FIELD not in reg_data
            and self.FEEDBACK_FIELD not in reg_data
            and self.ARC_FIELD not in reg_data
        )

        if missing_all:
            return VerifyResult.failure(
                MissingKeyError(
                    "Registry Missing Harmonic Safety Fields",
                    self._field,
                    "Older registry detected; no harmonic safety present.",
                ),
                severity=SeverityKind.WARNING,
                payload={
                    "missing_fields": [
                        field
                        for field in [
                            self.DREAMLINE_FIELD,
                            self.FEEDBACK_FIELD,
                            self.ARC_FIELD,
                        ]
                        if field not in reg_data
                    ]
                },
            )

        # ----------------------------
        # Base Field Validation (same as RuleHarmonicSafety)
        # ----------------------------

        dreamline = bool(fm_template.get_field(self.DREAMLINE_FIELD, False))

        # Mirrorwall Risk
        reg_risk: dict[str, Any] = reg_data[self.FEEDBACK_FIELD]
        default_risk = reg_risk.get("default_value", "low")
        feedback_val: str = fm_template.get_field(self.FEEDBACK_FIELD, default_risk)

        allowed_feedback = set(reg_risk.get("allowed_values", []))
        if feedback_val not in allowed_feedback:
            return VerifyResult.failure(
                VerifyError(
                    "Validation error:",
                    self.FEEDBACK_FIELD,
                    f"Invalid risk value '{feedback_val}'. Allowed: {', '.join(sorted(allowed_feedback))}",
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self.FEEDBACK_FIELD, "value": feedback_val},
            )

        # Arc Pressure
        reg_arc = reg_data[self.ARC_FIELD]
        default_arc = reg_arc.get("default_value", "none")
        arc_val: str = fm_template.get_field(self.ARC_FIELD, default_arc)

        allowed_arc = set(reg_arc.get("allowed_values", []))
        if arc_val not in allowed_arc:
            return VerifyResult.failure(
                VerifyError(
                    "Validation error:",
                    self.ARC_FIELD,
                    f"Invalid arc-pressure '{arc_val}'. Allowed: {', '.join(sorted(allowed_arc))}",
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self.ARC_FIELD, "value": arc_val},
            )

        # --------------------------------------------------------
        # COMPUTE ESCALATION TIER
        # --------------------------------------------------------
        tier = self._compute_escalation_tier(dreamline, feedback_val, arc_val)

        # Include tier in Result metadata for audit
        # (Your Result class already supports metadata injection)
        # But if not, it can be added later.

        # --------------------------------------------------------
        # APPLY ESCALATION RULES
        # --------------------------------------------------------

        # TIER 3 — CRITICAL ABORT
        if tier == 3:
            return VerifyResult.failure(
                SafetyAbortError(
                    "HARMONIC SAFETY CRITICAL (Tier 3)",
                    self._field,
                    f"Arc-pressure '{arc_val}' is severe. Rendering aborted to prevent structural Codex damage.",
                ),
                severity=SeverityKind.CRITICAL,
                payload={"field": self.ARC_FIELD, "value": arc_val},
            )

        # TIER 2 — RESTRICTED MODE
        if tier == 2:
            reg_profile = registry.get("field_being_profile", {})
            # Field Being required
            fb_required = fm_template.get_field(
                "invocation_requirement_field_being_required", True
            )
            if fb_required:
                if not reg_profile:
                    return VerifyResult.failure(
                        SafetyRestrictionError(
                            "HARMONIC SAFETY RESTRICTED (Tier 2)",
                            self._field,
                            "Restricted-mode invocation requires valid field-beings, but none found.",
                        ),
                        severity=SeverityKind.ERROR,
                        payload={"field": "field_being_profile", "registry": registry},
                    )

            # Witness Requirement
            witness_required = fm_template.get_field(
                "invocation_requirement_witness_required", False
            )
            if witness_required:
                if (
                    "witnessing_being" not in reg_profile
                    or not reg_profile["witnessing_being"]
                ):
                    return VerifyResult.failure(
                        SafetyRestrictionError(
                            "HARMONIC SAFETY RESTRICTED",
                            self._field,
                            "Restricted-mode invocation requires witness beings, but none present.",
                        ),
                        severity=SeverityKind.ERROR,
                        payload={"field": "witnessing_being", "registry": registry},
                    )

            # OK to proceed
            return VerifyResult.success(fm_template)

        # TIER 1 — CAUTION MODE (warn only)
        if tier == 1:
            return VerifyResult.failure(
                SafetyWarningError(
                    "HARMONIC SAFETY CAUTION (Tier 1)",
                    self._field,
                    f"Medium-level harmonic risk detected (feedback={feedback_val}, arc={arc_val}).",
                ),
                severity=SeverityKind.WARNING,
                payload={
                    "field": self._field,
                    "feedback": feedback_val,
                    "arc": arc_val,
                },
            )

        # TIER 0 — SAFE
        return VerifyResult.success(fm_template)
