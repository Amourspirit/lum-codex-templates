from typing import Any
from src.template.front_mater_meta import FrontMatterMeta
from api.lib.util.result import Result
from api.lib.exceptions import (
    VerifyError,
    MissingKeyError,
    SafetyAbortError,
    SafetyRestrictionError,
    SafetyWarningError,
)
from .protocol_verify_rule import ProtocolVerifyRule


class RuleHarmonicSafetyEscalation(ProtocolVerifyRule):
    """
    Harmonic Safety Validation + Escalation Logic

    Computes escalation tier from:
      - harmonic_safety_dreamline_instability  (bool)
      - harmonic_safety_mirrorwall_feedback_risk (enum)
      - harmonic_safety_arc_pressure (enum)

    Applies architectural restrictions on rendering and invocation safety.
    """

    DREAMLINE_FIELD = "harmonic_safety_dreamline_instability"
    FEEDBACK_FIELD = "harmonic_safety_mirrorwall_feedback_risk"
    ARC_FIELD = "harmonic_safety_arc_pressure"

    def __init__(self) -> None:
        self._field = self.DREAMLINE_FIELD

    def get_field(self) -> str:
        return self._field

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
    def validate(
        self, fm: FrontMatterMeta, registry: dict[str, Any]
    ) -> Result[bool, None] | Result[None, Exception]:

        reg_data = registry.get("metadata", registry)

        # Backward compatibility: if none present, report missing (warning)
        missing_all = (
            self.DREAMLINE_FIELD not in reg_data
            and self.FEEDBACK_FIELD not in reg_data
            and self.ARC_FIELD not in reg_data
        )

        if missing_all:
            return Result.failure(
                MissingKeyError(
                    "Registry Missing Harmonic Safety Fields",
                    self._field,
                    "Older registry detected; no harmonic safety present.",
                )
            )

        # ----------------------------
        # Base Field Validation (same as RuleHarmonicSafety)
        # ----------------------------

        dreamline = bool(fm.get_field(self.DREAMLINE_FIELD, False))

        # Mirrorwall Risk
        reg_risk: dict[str, Any] = reg_data[self.FEEDBACK_FIELD]
        default_risk = reg_risk.get("default_value", "low")
        feedback_val: str = fm.get_field(self.FEEDBACK_FIELD, default_risk)

        allowed_feedback = set(reg_risk.get("allowed_values", []))
        if feedback_val not in allowed_feedback:
            return Result.failure(
                VerifyError(
                    "Validation error:",
                    self.FEEDBACK_FIELD,
                    f"Invalid risk value '{feedback_val}'. Allowed: {', '.join(sorted(allowed_feedback))}",
                )
            )

        # Arc Pressure
        reg_arc = reg_data[self.ARC_FIELD]
        default_arc = reg_arc.get("default_value", "none")
        arc_val: str = fm.get_field(self.ARC_FIELD, default_arc)

        allowed_arc = set(reg_arc.get("allowed_values", []))
        if arc_val not in allowed_arc:
            return Result.failure(
                VerifyError(
                    "Validation error:",
                    self.ARC_FIELD,
                    f"Invalid arc-pressure '{arc_val}'. Allowed: {', '.join(sorted(allowed_arc))}",
                )
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
            return Result.failure(
                SafetyAbortError(
                    "HARMONIC SAFETY CRITICAL (Tier 3)",
                    self._field,
                    f"Arc-pressure '{arc_val}' is severe. Rendering aborted to prevent structural Codex damage.",
                )
            )

        # TIER 2 — RESTRICTED MODE
        if tier == 2:
            reg_profile = registry.get("field_being_profile", {})
            # Field Being required
            fb_required = fm.get_field(
                "invocation_requirement_field_being_required", True
            )
            if fb_required:
                if not reg_profile:
                    return Result.failure(
                        SafetyRestrictionError(
                            "HARMONIC SAFETY RESTRICTED (Tier 2)",
                            self._field,
                            "Restricted-mode invocation requires valid field-beings, but none found.",
                        )
                    )

            # Witness Requirement
            witness_required = fm.get_field(
                "invocation_requirement_witness_required", False
            )
            if witness_required:
                if (
                    "witnessing_being" not in reg_profile
                    or not reg_profile["witnessing_being"]
                ):
                    return Result.failure(
                        SafetyRestrictionError(
                            "HARMONIC SAFETY RESTRICTED",
                            self._field,
                            "Restricted-mode invocation requires witness beings, but none present.",
                        )
                    )

            # OK to proceed
            return Result.success(True)

        # TIER 1 — CAUTION MODE (warn only)
        if tier == 1:
            return Result.failure(
                SafetyWarningError(
                    "HARMONIC SAFETY CAUTION (Tier 1)",
                    self._field,
                    f"Medium-level harmonic risk detected (feedback={feedback_val}, arc={arc_val}).",
                )
            )

        # TIER 0 — SAFE
        return Result.success(True)
