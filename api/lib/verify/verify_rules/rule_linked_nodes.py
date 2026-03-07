from typing import Any, cast
from api.lib.protocols.protocol_rules_cache import ProtocolRulesCache
from src.template.front_mater_meta import FrontMatterMeta
from src.util.severity_kind import SeverityKind
from ..verify_result import VerifyResult
from ..exceptions import VerifyError, MissingKeyError
from .rule_verify import RuleVerify
from .types import PhaseInfo


class LinkedNodesRule(RuleVerify[PhaseInfo]):
    RULE_ORDER = 100

    def __init__(self, shared_cache: ProtocolRulesCache[PhaseInfo]) -> None:
        super().__init__(shared_cache)
        self._field = "linked_nodes"
        self._desc = "Validate that the 'linked_nodes' field is a list of numeric strings and that each corresponds to a valid node ID in the registry."

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

    def _is_numeric_string(self, s: str) -> bool:
        try:
            int(s)
            return True
        except ValueError:
            return False

    def apply(
        self,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> VerifyResult[FrontMatterMeta, None] | VerifyResult[None, VerifyError]:

        fields = cast(dict[str, Any], registry.get("fields", {}))
        if self._field not in fields:
            return VerifyResult.failure(
                MissingKeyError(
                    f"Missing Key error in field '{self._field}': ",
                    self._field,
                    f"Field '{self._field}' is not defined in the registry.",
                ),
                severity=SeverityKind.WARNING,
                payload={"field": self._field},
            )
        if not fm_template.has_field(self._field):
            return VerifyResult.failure(
                MissingKeyError(
                    f"Missing Key error in field '{self._field}': ",
                    self._field,
                    f"Field '{self._field}' is required but not found in the frontmatter.",
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self._field},
            )
        value = fm_template.get_field(self._field)
        if not isinstance(value, list):
            return VerifyResult.failure(
                VerifyError(
                    f"Field '{self._field}' must be a list.",
                    self._field,
                    f"Field '{self._field}' is expected to be a list of numeric strings, but got {type(value).__name__}.",
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self._field, "value": value},
            )
        errors: list[str] = []

        for item in value:
            if not isinstance(item, str):
                errors.append(f"Item '{item}' is not a string.")
            else:
                if not self._is_numeric_string(item):
                    errors.append(f"Item '{item}' is not a numeric string.")
        if errors:
            return VerifyResult.failure(
                VerifyError(
                    f"Validation errors in field '{self._field}': ",
                    self._field,
                    errors,
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self._field, "value": value, "errors": errors},
            )
        return VerifyResult.success(fm_template)
