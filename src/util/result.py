from __future__ import annotations
from typing import TypeVar, Union, Generic, Iterator, Tuple, Any
from typing import TypeIs
from loguru import logger
from .severity_kind import SeverityKind

T = TypeVar("T")  # Type for success value
E = TypeVar("E", bound=BaseException | None)  # Type for error value
T_Success = TypeVar("T_Success")
E_Failure = TypeVar("E_Failure", bound=BaseException)


class Result(Generic[T, E]):
    """
    A generic Result type that represents either:
        - a successful outcome (data != None, error == None), or
        - a failure outcome   (data == None, error != None)

    Now includes:
        severity : SeverityKind | None
        payload  : Any (optional structured metadata)

    This class is used extensively by UpgradeEngine and rule implementations.
    """

    def __init__(
        self,
        data: T,
        error: E,
        severity: SeverityKind | None = None,
        payload: Any = None,
    ) -> None:
        self.data: T = data
        self.error: E = error
        self.severity: SeverityKind | None = severity
        self.payload: Any = payload
        # Defensive validation warning
        if (self.data is not None) and (self.error is not None):
            logger.warning(
                f"Invalid Result state: both data and error are set. "
                f"This is usually unintended. data={self.data!r}, error={self.error!r}"
            )

    # --------------------------------------------------------------
    # Representation & utility
    # --------------------------------------------------------------

    def __bool__(self) -> bool:
        """A Result is truthy if and only if it represents success."""
        return self.error is None

    def __repr__(self) -> str:
        return (
            "Result("
            f"data={repr(self.data)}, "
            f"error={repr(self.error)}, "
            f"severity={self.severity}, "
            f"payload={repr(self.payload)})"
        )

    def __iter__(self) -> Iterator[Union[T, E]]:
        """Useful for quick unpacking."""
        return iter((self.data, self.error))

    def unpack(self) -> Tuple[T, E]:
        """Return (data, error) tuple."""
        return (self.data, self.error)

    def is_warning(self) -> bool:
        """Return True if the Result has severity WARNING."""
        return self.severity == SeverityKind.WARNING

    def is_error(self) -> bool:
        """Return True if the Result has severity ERROR."""
        return self.severity == SeverityKind.ERROR

    def is_critical(self) -> bool:
        """Return True if the Result has severity CRITICAL."""
        return self.severity == SeverityKind.CRITICAL

    # region Properties
    @property
    def message(self) -> str | None:
        return self.payload if isinstance(self.payload, str) else None

    # endregion Properties

    # --------------------------------------------------------------
    # Constructors
    # --------------------------------------------------------------

    @staticmethod
    def success(
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
        return Result(data=data, error=None, severity=severity, payload=payload)

    @staticmethod
    def failure(
        error: E_Failure,
        severity: SeverityKind = SeverityKind.ERROR,
        payload: Any = None,
    ) -> "Result[None, E_Failure]":
        """
        Create a failure Result.

        Args:
            error: Exception describing the failure
            severity: Optional SeverityKind level (default: ERROR)
            payload: Optional structured metadata

        Returns:
            Result object with data=None
        """
        return Result(data=None, error=error, severity=severity, payload=payload)

    # --------------------------------------------------------------
    # Type guards
    # --------------------------------------------------------------

    @staticmethod
    def is_success(
        obj: Union["Result[T_Success, None]", "Result[None, E_Failure]"],
    ) -> TypeIs["Result[T_Success, None]"]:
        """Return True if the Result represents success."""
        return isinstance(obj, Result) and obj.error is None

    @staticmethod
    def is_failure(
        obj: Union["Result[T_Success, None]", "Result[None, E_Failure]"],
    ) -> TypeIs["Result[None, E_Failure]"]:
        """Return True if the Result represents failure."""
        return isinstance(obj, Result) and obj.error is not None
