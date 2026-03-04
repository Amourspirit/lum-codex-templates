from __future__ import annotations
from typing import Generic, TypeVar, Union, Any, TypeIs
from src.util.severity_kind import SeverityKind as SeverityKind
from src.util.result_base import ResultBase, T
from .exceptions import UpgradeError

E = TypeVar("E", bound=UpgradeError | None, covariant=True)  # Type for error value
E_Failure = TypeVar("E_Failure", bound=UpgradeError, covariant=True)
T_Success = TypeVar("T_Success")

# F-bounded type for concrete subclasses
Self = TypeVar("Self", bound="UpgradeResult[Any, Any]")


# Concrete Result class with Exception-bound errors
class UpgradeResult(ResultBase[T, UpgradeError | None], Generic[T, E]):
    """Upgrade Result with UpgradeError-bound errors."""

    @classmethod
    def success(
        cls: type[Self],
        data: T_Success,
        severity: SeverityKind = SeverityKind.INFO,
        payload: Any = None,
    ) -> "UpgradeResult[T_Success, None]":
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
        error: E_Failure,
        severity: SeverityKind = SeverityKind.ERROR,
        payload: Any = None,
    ) -> "UpgradeResult[None, E_Failure]":
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
        obj: Union["UpgradeResult[T_Success, None]", "UpgradeResult[None, E_Failure]"],
    ) -> TypeIs["UpgradeResult[T_Success, None]"]:
        """Return True if the UpgradeResult represents success."""
        return isinstance(obj, UpgradeResult) and obj.error is None

    @classmethod
    def is_failure(
        cls: type[Self],
        obj: Union["UpgradeResult[T_Success, None]", "UpgradeResult[None, E_Failure]"],
    ) -> TypeIs["UpgradeResult[None, E_Failure]"]:
        """Return True if the UpgradeResult represents failure."""
        return isinstance(obj, UpgradeResult) and obj.error is not None
