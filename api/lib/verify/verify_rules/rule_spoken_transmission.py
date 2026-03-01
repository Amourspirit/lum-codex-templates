from typing import Any

from src.template.front_mater_meta import FrontMatterMeta
from api.lib.util.result import Result
from api.lib.exceptions import VerifyError
from .protocol_verify_rule import ProtocolVerifyRule


class RuleSpokenTransmission(ProtocolVerifyRule):
    def __init__(self) -> None:
        self._field = "multi_field_spoken_transmission_rule"

    def get_field(self) -> str:
        return self._field

    def validate(
        self, fm: FrontMatterMeta, registry: dict[str, Any]
    ) -> Result[bool, None] | Result[None, Exception]:

        # fields = cast(dict[str, Any], registry.get("fields", {}))

        # --- Extract all relevant fields ---

        fmt: str | None = fm.get_field("voice_transmission_format")
        hst: bool = fm.get_field("has_spoken_transmission", False)
        sl: str | None = fm.get_field("spoken_line")
        vcb: str | None = fm.get_field("voice_confirmed_by")
        rsr: bool = fm.get_field("invocation_requirement_spoken_line_required", False)

        # --- EARLY EXIT: No vocal metadata present ---
        # If the template does not use ANY spoken-transmission fields,
        # the rule should not activate.
        if fmt is None and not hst and sl is None and vcb is None and not rsr:
            return Result.success(True)

        # 1. FORMAT ALIGNMENT
        # voice_transmission_format allowed_values:
        #   - spoken
        #   - text
        #   - hybrid
        #   - none

        # 'text' format is valid and does not imply spoken transmission.
        # No special constraint applies unless hst or sl or vcb or rsr is set.

        if fmt in ("spoken", "hybrid") and not hst:
            return Result.failure(
                VerifyError(
                    "Validation error:",
                    self._field,
                    f"voice_transmission_format='{fmt}' implies spoken transmission, but has_spoken_transmission is false.",
                )
            )

        if fmt == "none":
            if hst:
                return Result.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "voice_transmission_format is missing or null but has_spoken_transmission=true.",
                    )
                )
            if sl:
                return Result.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "voice_transmission_format is missing or null but spoken_line is populated.",
                    )
                )
            if vcb:
                return Result.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "voice_transmission_format is missing or null but voice_confirmed_by is set.",
                    )
                )

        # 2. SPOKEN LINE VALIDATION
        if hst and (sl is None or not str(sl).strip()):
            return Result.failure(
                VerifyError(
                    "Validation error:",
                    self._field,
                    "has_spoken_transmission=true but spoken_line is missing or empty.",
                )
            )

        if not hst and sl:
            return Result.failure(
                VerifyError(
                    "Validation error:",
                    self._field,
                    "spoken_line is populated but has_spoken_transmission=false.",
                )
            )

        # 3. INVOCATION REQUIREMENTS
        if rsr:
            if not hst:
                return Result.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "invocation requires spoken transmission but has_spoken_transmission=false.",
                    )
                )
            if sl is None or not str(sl).strip():
                return Result.failure(
                    VerifyError(
                        "Validation error:",
                        self._field,
                        "invocation requires spoken_line but it is missing.",
                    )
                )

        # 4. VOICE CONFIRMATION
        if hst and (vcb is None or not str(vcb).strip()):
            return Result.failure(
                VerifyError(
                    "Validation error:",
                    self._field,
                    "Spoken transmission present but voice_confirmed_by is missing.",
                )
            )

        if not hst and vcb:
            return Result.failure(
                VerifyError(
                    "Validation error:",
                    self._field,
                    "voice_confirmed_by present but has_spoken_transmission=false.",
                )
            )

        return Result.success(True)
