from typing import Any
from src.template.front_mater_meta import FrontMatterMeta
from api.lib.util.result import Result
from api.lib.exceptions import VerifyError
from .protocol_verify_rule import ProtocolVerifyRule


class RuleWitnessRequirement(ProtocolVerifyRule):
    """
    Enforces consistency when witness confirmation is required
    for sigils, seals, scrolls, or any invocation-bearing artifact.
    """

    def __init__(self) -> None:
        self._field = "witnessing_being"

    def get_field(self) -> str:
        return self._field

    def validate(
        self, fm: FrontMatterMeta, registry: dict[str, Any]
    ) -> Result[bool, None] | Result[None, Exception]:

        w_required: bool = fm.get_field(
            "invocation_requirement_witness_required", False
        )
        witness: list[str] | None = fm.get_field(self._field)

        # --- EARLY EXIT: No invocation witness logic in template ---
        if not w_required and witness is None:
            return Result.success(True)

        # --- WITNESS REQUIRED ---
        if w_required:
            if witness is None:
                return Result.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "Invocation requires a witness, but 'witnessing_being' is missing.",
                    )
                )

            # Must be list-like
            if not isinstance(witness, list):
                return Result.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "'witnessing_being' must be a list when witness is required.",
                    )
                )

            # Must contain at least one meaningful entry
            if not witness or all(not str(w).strip() for w in witness):
                return Result.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "Invocation requires at least one valid witnessing being.",
                    )
                )

        # --- WITNESS NOT REQUIRED ---
        # No additional constraints. Whitespace-only or empty entries
        # can be cleaned by upstream or left alone.
        return Result.success(True)
