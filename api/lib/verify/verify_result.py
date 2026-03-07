from __future__ import annotations
from typing import TypeVar, Union, Any, TypeIs
from src.util.severity_kind import SeverityKind as SeverityKind
from src.util.result_base import ResultBase, T
from .exceptions import VerifyError

T_E = TypeVar("T_E", bound=VerifyError | None)
T_Verify_Failure = TypeVar("T_Verify_Failure", bound=VerifyError)
T_Verify_Success = TypeVar("T_Verify_Success")

# F-bounded type for concrete subclasses
Self = TypeVar("Self", bound="VerifyResult[Any, Any]")


# Concrete Result class with Exception-bound errors
class VerifyResult(ResultBase[T, T_E]):
    """Verify Result with VerifyError-bound errors."""

    @classmethod
    def success(
        cls: type[Self],
        data: T_Verify_Success,
        severity: SeverityKind = SeverityKind.INFO,
        payload: Any = None,
    ) -> "VerifyResult[T_Verify_Success, None]":
        """
        Create a successful VerifyResult.

        Args:
            data: Success value
            severity: Optional SeverityKind level (default: INFO)
            payload: Optional structured metadata

        Returns:
            UpgradeSuccess object with error=None
        """
        return cls(data=data, error=None, severity=severity, payload=payload)

    @classmethod
    def failure(
        cls: type[Self],
        error: T_Verify_Failure,
        severity: SeverityKind = SeverityKind.ERROR,
        payload: Any = None,
    ) -> "VerifyResult[None, T_Verify_Failure]":
        """
        Create a failure Result.

        Args:
            error: VerifyError or subclass describing the failure
            severity: Optional SeverityKind level (default: ERROR)
            payload: Optional structured metadata

        Returns:
            UpgradeResult object with data=None
        """

        return cls(data=None, error=error, severity=severity, payload=payload)

    @classmethod
    def is_success(
        cls,
        obj: Union[
            "VerifyResult[T_Verify_Success, None]",
            "VerifyResult[None, T_Verify_Failure]",
        ],
    ) -> TypeIs["VerifyResult[T_Verify_Success, None]"]:
        """
        Type guard to check if a Result instance represents success.

        Static method.

        Args:
            obj: The Result instance to check

        Returns:
            True if the Result represents success, False otherwise
        """
        return isinstance(obj, VerifyResult) and obj.result_is_success()

    @classmethod
    def is_failure(
        cls,
        obj: Union[
            "VerifyResult[T_Verify_Success, None]",
            "VerifyResult[None, T_Verify_Failure]",
        ],
    ) -> TypeIs["VerifyResult[None, T_Verify_Failure]"]:
        """
        Type guard to check if a Result instance represents failure.

        Static method.

        Args:
            obj: The Result instance to check

        Returns:
            True if the Result represents failure, False otherwise
        """
        return isinstance(obj, VerifyResult) and obj.result_is_failure()
