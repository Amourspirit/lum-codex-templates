from typing import Any
from api.lib.protocols.protocol_rules_cache import ProtocolRulesCache
from src.template.front_mater_meta import FrontMatterMeta
from src.util.severity_kind import SeverityKind
from ..verify_result import VerifyResult
from ..exceptions import VerifyError
from .rule_verify import RuleVerify
from .types import PhaseInfo


class RuleWitnessRequirement(RuleVerify[PhaseInfo]):
    """
    Enforces consistency when witness confirmation is required
    for sigils, seals, scrolls, or any invocation-bearing artifact.
    """

    RULE_ORDER = 100

    def __init__(self, shared_cache: ProtocolRulesCache[PhaseInfo]) -> None:
        super().__init__(shared_cache)
        self._field = "witnessing_being"
        self._desc = "Validate that if invocation requires a witnessing being, the 'witnessing_being' field is present and contains at least one valid entry."

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

        w_required: bool = fm_template.get_field(
            "invocation_requirement_witness_required", False
        )
        witness: list[str] | None = fm_template.get_field(self._field)

        # --- EARLY EXIT: No invocation witness logic in template ---
        if not w_required and witness is None:
            return VerifyResult.success(fm_template)

        # --- WITNESS REQUIRED ---
        if w_required:
            if witness is None:
                return VerifyResult.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "Invocation requires a witness, but 'witnessing_being' is missing.",
                    ),
                    severity=SeverityKind.WARNING,
                    payload={"field": self._field},
                )

            # Must be list-like
            if not isinstance(witness, list):
                return VerifyResult.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "'witnessing_being' must be a list when witness is required.",
                    ),
                    severity=SeverityKind.ERROR,
                    payload={"field": self._field, "value": witness},
                )

            # Must contain at least one meaningful entry
            if not witness or all(not str(w).strip() for w in witness):
                return VerifyResult.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "Invocation requires at least one valid witnessing being.",
                    ),
                    severity=SeverityKind.WARNING,
                    payload={"field": self._field, "value": witness},
                )

        # --- WITNESS NOT REQUIRED ---
        # No additional constraints. Whitespace-only or empty entries
        # can be cleaned by upstream or left alone.
        return VerifyResult.success(fm_template)
