from __future__ import annotations
from typing import Generic, TypeVar, Union, Any, TypeIs
from .severity_kind import SeverityKind
from .result_base import ResultBase, T

E = TypeVar("E", bound=BaseException | None, covariant=True)  # Type for error value
E_Failure = TypeVar("E_Failure", bound=BaseException, covariant=True)
T_Success = TypeVar("T_Success")

# F-bounded type for concrete subclasses
Self = TypeVar("Self", bound="Result[Any, Any]")


# Concrete Result class with Exception-bound errors
class Result(ResultBase[T, BaseException | None], Generic[T, E]):
    """Standard Result with Exception-bound errors."""

    @classmethod
    def success(
        cls: type[Self],
        data: T_Success,
        severity: SeverityKind = SeverityKind.INFO,
        payload: Any = None,
    ) -> "Result[T_Success, None]":
        """
        Create a successful Result.

        Args:
            data: Success value
            severity: Optional SeverityKind level (default: INFO)
            payload: Optional structured metadata

        Returns:
            Result object with error=None
        """
        return cls(data=data, error=None, severity=severity, payload=payload)

    @classmethod
    def failure(
        cls: type[Self],
        error: E_Failure,
        severity: SeverityKind = SeverityKind.ERROR,
        payload: Any = None,
    ) -> "Result[None, E_Failure]":
        """
        Create a failure Result.

        Args:
            error: Exception or subclass describing the failure
            severity: Optional SeverityKind level (default: ERROR)
            payload: Optional structured metadata

        Returns:
            Result object with data=None
        """
        return cls(data=None, error=error, severity=severity, payload=payload)

    @classmethod
    def is_success(
        cls: type[Self],
        obj: Union["Result[T_Success, None]", "Result[None, E_Failure]"],
    ) -> TypeIs["Result[T_Success, None]"]:
        """Return True if the Result represents success."""
        return isinstance(obj, Result) and obj.error is None

    @classmethod
    def is_failure(
        cls: type[Self],
        obj: Union["Result[T_Success, None]", "Result[None, E_Failure]"],
    ) -> TypeIs["Result[None, E_Failure]"]:
        """Return True if the Result represents failure."""
        return isinstance(obj, Result) and obj.error is not None
