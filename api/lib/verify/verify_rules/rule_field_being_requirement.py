from typing import Any
from src.template.front_mater_meta import FrontMatterMeta
from api.lib.util.result import Result
from api.lib.exceptions import VerifyError, MissingKeyError
from .protocol_verify_rule import ProtocolVerifyRule


class RuleFieldBeingRequirement(ProtocolVerifyRule):
    """
    Ensures that at least one valid field-being is present when
    invocation_requirement_field_being_required=true.
    """

    def __init__(self) -> None:
        self._field = "invocation_requirement_field_being_required"

    def get_field(self) -> str:
        return self._field

    def validate(
        self, fm: FrontMatterMeta, registry: dict[str, Any]
    ) -> Result[bool, None] | Result[None, Exception]:

        fb_required: bool = fm.get_field(self._field, False)

        # Support registry layouts with or without metadata wrapper
        reg_data = registry.get("metadata", registry)

        # Backwards compatibility: old registries won't include field_being_profile
        if "field_being_profile" not in reg_data:
            return Result.failure(
                MissingKeyError(
                    "Registry Missing Key: field_being_profile",
                    self._field,
                    "Registry must include 'field_being_profile' for field-being requirement validation.",
                )
            )

        reg_profile = reg_data.get("field_being_profile")

        # EARLY EXIT: If field-beings not required and no profile, skip rule
        if not fb_required and reg_profile is None:
            return Result.success(True)

        # FIELD-BEING REQUIRED
        if fb_required:
            # Must exist
            if reg_profile is None:
                return Result.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        f"Invocation requires a field being, but 'field_being_profile' is missing for {fm.template_type} in registry.",
                    )
                )

            # Must be dict
            if not isinstance(reg_profile, dict):
                return Result.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "Registry 'field_being_profile' must be a dictionary.",
                    )
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
                return Result.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "Invocation requires at least one valid field-being, but none were found.",
                    )
                )

        return Result.success(True)
