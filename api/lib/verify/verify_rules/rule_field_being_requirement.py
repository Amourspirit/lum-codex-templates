from typing import Any
from api.lib.protocols.protocol_rules_cache import ProtocolRulesCache
from src.template.front_mater_meta import FrontMatterMeta
from src.util.severity_kind import SeverityKind
from ..verify_result import VerifyResult
from ..exceptions import VerifyError, MissingKeyError
from .rule_verify import RuleVerify
from .types import PhaseInfo


class RuleFieldBeingRequirement(RuleVerify[PhaseInfo]):
    """
    Ensures that at least one valid field-being is present when
    invocation_requirement_field_being_required=true.
    """

    RULE_ORDER = 100

    def __init__(self, shared_cache: ProtocolRulesCache[PhaseInfo]) -> None:
        super().__init__(shared_cache)
        self._field = "invocation_requirement_field_being_required"
        self._desc = "Validate that if invocation requires a field-being, at least one valid field-being is present in the registry."

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

    def apply(
        self,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> VerifyResult[FrontMatterMeta, None] | VerifyResult[None, VerifyError]:

        fb_required: bool = fm_template.get_field(self._field, False)

        # Support registry layouts with or without metadata wrapper
        reg_data = registry.get("metadata", registry)

        # Backwards compatibility: old registries won't include field_being_profile
        if "field_being_profile" not in reg_data:
            return VerifyResult.failure(
                MissingKeyError(
                    "Registry Missing Key: field_being_profile",
                    self._field,
                    "Registry must include 'field_being_profile' for field-being requirement validation.",
                ),
                severity=SeverityKind.WARNING,
                payload={"field": self._field},
            )

        reg_profile = reg_data.get("field_being_profile")

        # EARLY EXIT: If field-beings not required and no profile, skip rule
        if not fb_required and reg_profile is None:
            return VerifyResult.success(fm_template)

        # FIELD-BEING REQUIRED
        if fb_required:
            # Must exist
            if reg_profile is None:
                return VerifyResult.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        f"Invocation requires a field being, but 'field_being_profile' is missing for {fm_template.template_type} in registry.",
                    ),
                    severity=SeverityKind.ERROR,
                    payload={"field": self._field},
                )

            # Must be dict
            if not isinstance(reg_profile, dict):
                return VerifyResult.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "Registry 'field_being_profile' must be a dictionary.",
                    ),
                    severity=SeverityKind.ERROR,
                    payload={"field": self._field},
                )

            # --- MICRO-OPTIMIZATION: Validate beings across all roles ---
            found_being = False

            allowed_beings = registry.get("allowed_beings")

            for role, beings in reg_profile.items():
                # Skip malformed role entries
                if not isinstance(beings, list):
                    continue

                for b in beings:
                    if b is None:
                        continue

                    b_str = str(b).strip()
                    if not b_str:
                        continue

                    # Optional future semantic constraint
                    if allowed_beings is not None:
                        if isinstance(allowed_beings, list):
                            if b_str not in allowed_beings:
                                continue
                        elif isinstance(allowed_beings, dict):
                            allowed_for_role = allowed_beings.get(role, [])
                            if b_str not in allowed_for_role:
                                continue

                    # Valid being found
                    found_being = True
                    break

                if found_being:
                    break

            # If no valid being found after all roles, fail
            if not found_being:
                return VerifyResult.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "Invocation requires at least one valid field-being, but none were found.",
                    ),
                    severity=SeverityKind.ERROR,
                    payload={"field": self._field},
                )

        return VerifyResult.success(fm_template)
