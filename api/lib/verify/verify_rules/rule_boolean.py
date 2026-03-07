from typing import Any, cast, TypeVar, Generic
from api.lib.protocols import ProtocolRulesCache
from src.template.front_mater_meta import FrontMatterMeta
from src.util.severity_kind import SeverityKind
from ..verify_result import VerifyResult
from .rule_verify import RuleVerify
from .types import PhaseInfo
from ..exceptions import (
    VerifyError,
    MissingKeyError,
    RequiredFieldMissingError,
    NullFieldError,
)

T = TypeVar("T")


class RuleBoolean(RuleVerify[T], Generic[T]):
    RULE_ORDER = 100

    def __init__(self, shared_cache: ProtocolRulesCache[T], field: str) -> None:
        super().__init__(shared_cache)
        self._field = field
        self._desc = f"Validate that field '{self._field}' is a boolean value."

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
        reg_data = self._get_registry_data(registry)

        fields = cast(dict[str, Any], reg_data.get("fields", {}))
        field_data = fields.get(self._field, {})
        if not field_data:
            return VerifyResult.failure(
                VerifyError(
                    f"No field data found in registry '{self._field}': ",
                    self._field,
                    f"Field '{self._field}' is not defined in the registry.",
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self._field},
            )

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

        field_required = field_data.get("required", False)

        if field_required and not fm_template.has_field(self._field):
            return VerifyResult.failure(
                RequiredFieldMissingError(
                    f"Required field '{self._field}' is missing: ",
                    self._field,
                    f"Field '{self._field}' is required but not found in the frontmatter.",
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self._field},
            )

        field_nullable = field_data.get("nullable", False)

        value = fm_template.get_field(self._field)
        if value is None:
            if field_nullable:
                return VerifyResult.success(fm_template)
            else:
                return VerifyResult.failure(
                    NullFieldError(
                        f"Null field error in field '{self._field}': ",
                        self._field,
                        f"Field '{self._field}' cannot be null.",
                    ),
                    severity=SeverityKind.ERROR,
                    payload={"field": self._field},
                )

        if not isinstance(value, bool):
            return VerifyResult.failure(
                VerifyError(
                    f"Validation error in field '{self._field}': ",
                    self._field,
                    f"Value for field '{self._field}' must be a boolean",
                ),
                severity=SeverityKind.ERROR,
                payload={"field": self._field},
            )
        return VerifyResult.success(fm_template)
