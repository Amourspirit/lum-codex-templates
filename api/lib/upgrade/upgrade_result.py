from __future__ import annotations
from typing import Generic, TypeVar, Union, Any, TypeIs
from src.util.severity_kind import SeverityKind as SeverityKind
from src.util.result_base import ResultBase, T
from .exceptions import UpgradeError

T_E = TypeVar("T_E", bound=UpgradeError | None, covariant=True)  # Type for error value
T_Upgrade_Failure = TypeVar("T_Upgrade_Failure", bound=UpgradeError, covariant=True)
T_Upgrade_Success = TypeVar("T_Upgrade_Success")

# F-bounded type for concrete subclasses
Self = TypeVar("Self", bound="UpgradeResult[Any, Any]")


# Concrete Result class with Exception-bound errors
class UpgradeResult(ResultBase[T, T_E]):
    """Upgrade Result with UpgradeError-bound errors."""

    @classmethod
    def success(
        cls: type[Self],
        data: T_Upgrade_Success,
        severity: SeverityKind = SeverityKind.INFO,
        payload: Any = None,
    ) -> "UpgradeResult[T_Upgrade_Success, None]":
        """
        Create a successful UpgradeResult.

        Args:
            data: Success value
            severity: Optional SeverityKind level (default: INFO)
            payload: Optional structured metadata

        Returns:
            UpgradeResult object with error=None
        """
        return cls(data=data, error=None, severity=severity, payload=payload)

    @classmethod
    def failure(
        cls: type[Self],
        error: T_Upgrade_Failure,
        severity: SeverityKind = SeverityKind.ERROR,
        payload: Any = None,
    ) -> "UpgradeResult[None, T_Upgrade_Failure]":
        """
        Create a failure Result.

        Args:
            error: UpgradeError or subclass describing the failure
            severity: Optional SeverityKind level (default: ERROR)
            payload: Optional structured metadata

        Returns:
            UpgradeResult object with data=None
        """
        return cls(data=None, error=error, severity=severity, payload=payload)

    @classmethod
    def is_success(
        cls: type[Self],
        obj: Union[
            "UpgradeResult[T_Upgrade_Success, None]",
            "UpgradeResult[None, T_Upgrade_Failure]",
        ],
    ) -> TypeIs["UpgradeResult[T_Upgrade_Success, None]"]:
        """Return True if the UpgradeResult represents success."""
        return isinstance(obj, UpgradeResult) and obj.error is None

    @classmethod
    def is_failure(
        cls: type[Self],
        obj: Union[
            "UpgradeResult[T_Upgrade_Success, None]",
            "UpgradeResult[None, T_Upgrade_Failure]",
        ],
    ) -> TypeIs["UpgradeResult[None, T_Upgrade_Failure]"]:
        """Return True if the UpgradeResult represents failure."""
        return isinstance(obj, UpgradeResult) and obj.error is not None
