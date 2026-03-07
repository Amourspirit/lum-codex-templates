from typing import Any
from api.lib.protocols.protocol_rules_cache import ProtocolRulesCache
from src.template.front_mater_meta import FrontMatterMeta
from src.util.severity_kind import SeverityKind
from ..verify_result import VerifyResult
from ..exceptions import VerifyError
from .rule_verify import RuleVerify
from .types import PhaseInfo


class RuleSpokenTransmission(RuleVerify[PhaseInfo]):
    RULE_ORDER = 100

    def __init__(self, shared_cache: ProtocolRulesCache[PhaseInfo]) -> None:
        super().__init__(shared_cache)
        self._field = "multi_field_spoken_transmission_rule"
        self._desc = "Validate that spoken transmission metadata fields are consistent and meet invocation requirements."

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

        # fields = cast(dict[str, Any], registry.get("fields", {}))

        # --- Extract all relevant fields ---

        fmt: str | None = fm_template.get_field("voice_transmission_format")
        hst: bool = fm_template.get_field("has_spoken_transmission", False)
        sl: str | None = fm_template.get_field("spoken_line")
        vcb: str | None = fm_template.get_field("voice_confirmed_by")
        rsr: bool = fm_template.get_field(
            "invocation_requirement_spoken_line_required", False
        )

        # --- EARLY EXIT: No vocal metadata present ---
        # If the template does not use ANY spoken-transmission fields,
        # the rule should not activate.
        if fmt is None and not hst and sl is None and vcb is None and not rsr:
            return VerifyResult.success(fm_template)

        # 1. FORMAT ALIGNMENT
        # voice_transmission_format allowed_values:
        #   - spoken
        #   - text
        #   - hybrid
        #   - none

        # 'text' format is valid and does not imply spoken transmission.
        # No special constraint applies unless hst or sl or vcb or rsr is set.

        if fmt in ("spoken", "hybrid") and not hst:
            return VerifyResult.failure(
                VerifyError(
                    "Validation error:",
                    self._field,
                    f"voice_transmission_format='{fmt}' implies spoken transmission, but has_spoken_transmission is false.",
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self._field, "value": fmt},
            )

        if fmt == "none":
            if hst:
                return VerifyResult.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "voice_transmission_format is missing or null but has_spoken_transmission=true.",
                    ),
                    severity=SeverityKind.ERROR,
                    payload={"field": self._field, "value": fmt},
                )
            if sl:
                return VerifyResult.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "voice_transmission_format is missing or null but spoken_line is populated.",
                    ),
                    severity=SeverityKind.ERROR,
                    payload={"field": self._field, "value": fmt},
                )
            if vcb:
                return VerifyResult.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "voice_transmission_format is missing or null but voice_confirmed_by is set.",
                    ),
                    severity=SeverityKind.ERROR,
                    payload={"field": self._field, "value": fmt},
                )

        # 2. SPOKEN LINE VALIDATION
        if hst and (sl is None or not str(sl).strip()):
            return VerifyResult.failure(
                VerifyError(
                    "Validation error:",
                    self._field,
                    "has_spoken_transmission=true but spoken_line is missing or empty.",
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self._field, "value": hst},
            )

        if not hst and sl:
            return VerifyResult.failure(
                VerifyError(
                    "Validation error:",
                    self._field,
                    "spoken_line is populated but has_spoken_transmission=false.",
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self._field, "value": sl},
            )

        # 3. INVOCATION REQUIREMENTS
        if rsr:
            if not hst:
                return VerifyResult.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "invocation requires spoken transmission but has_spoken_transmission=false.",
                    ),
                    severity=SeverityKind.ERROR,
                    payload={"field": self._field, "value": rsr},
                )
            if sl is None or not str(sl).strip():
                return VerifyResult.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "invocation requires spoken_line but it is missing.",
                    ),
                    severity=SeverityKind.ERROR,
                    payload={"field": self._field, "value": rsr},
                )

        # 4. VOICE CONFIRMATION
        if hst and (vcb is None or not str(vcb).strip()):
            return VerifyResult.failure(
                VerifyError(
                    "Validation error:",
                    self._field,
                    "Spoken transmission present but voice_confirmed_by is missing.",
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self._field, "value": hst},
            )

        if not hst and vcb:
            return VerifyResult.failure(
                VerifyError(
                    "Validation error:",
                    self._field,
                    "voice_confirmed_by present but has_spoken_transmission=false.",
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self._field, "value": vcb},
            )

        return VerifyResult.success(fm_template)
