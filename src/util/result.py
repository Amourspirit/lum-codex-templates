from __future__ import annotations
from typing import TypeVar, Union, Any, TypeIs, cast
from .severity_kind import SeverityKind
from .result_base import ResultBase, T

E = TypeVar("E", bound=BaseException | None)  # Type for error value
E_Failure = TypeVar("E_Failure", bound=BaseException)
T_Success = TypeVar("T_Success")

# F-bounded type for concrete subclasses
Self = TypeVar("Self", bound="Result[Any, Any]")


# Concrete Result class with Exception-bound errors
class Result(ResultBase[T, E]):
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
        cls,
        obj: Union[
            "Result[T_Success, None]",
            "Result[None, E_Failure]",
        ],
    ) -> TypeIs["Result[T_Success, None]"]:
        """
        Type guard to check if a Result instance represents success.

        Static method.

        Args:
            obj: The Result instance to check

        Returns:
            True if the Result represents success, False otherwise
        """
        return isinstance(obj, Result) and obj.result_is_success()

    @classmethod
    def is_failure(
        cls,
        obj: Union[
            "Result[T_Success, None]",
            "Result[None, E_Failure]",
        ],
    ) -> TypeIs["Result[None, E_Failure]"]:
        """
        Type guard to check if a Result instance represents failure.

        Static method.

        Args:
            obj: The Result instance to check

        Returns:
            True if the Result represents failure, False otherwise
        """
        return isinstance(obj, Result) and obj.result_is_failure()


# if __name__ == "__main__":
#     success = Result.success("Some Data")
#     failure = Result.failure(ValueError("Something went wrong"))
#     obj = cast(Union[Result[str, None], Result[None, ValueError]], success)
#     assert success.data == "Some Data"
#     assert success.error is None
#     assert failure.data is None
#     assert isinstance(failure.error, ValueError)

#     if Result.is_success(obj):
#         assert obj.data == "Some Data"
#         assert obj.error is None
#     else:
#         assert obj.data is None
#         assert isinstance(obj.error, ValueError)

#     if Result.is_failure(obj):
#         assert obj.data is None
#         assert isinstance(obj.error, ValueError)
#     else:
#         assert obj.data == "Some Data"
#         assert obj.error is None
