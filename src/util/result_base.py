from __future__ import annotations
from typing import TypeVar, Union, Generic, Iterator, Tuple, Any
from loguru import logger
from .severity_kind import SeverityKind

T = TypeVar("T")  # Type for success value
E = TypeVar("E", covariant=True)

# F-bounded type for concrete subclasses
Self = TypeVar("Self", bound="ResultBase[Any, Any]")


class ResultBase(Generic[T, E]):
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
            f"{self.__class__.__name__}("
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

    @classmethod
    def success(
        cls: type[Self],
        data: Any,
        severity: SeverityKind = SeverityKind.INFO,
        payload: Any = None,
    ) -> Self:
        """
        Create a successful Result.

        Args:
            data: Success value
            severity: Optional SeverityKind level (default: INFO)
            payload: Optional structured metadata

        Returns:
            Result object with error=None
        """
        return cls(data=data, error=None, severity=severity, payload=payload)  # type: ignore

    @classmethod
    def failure(
        cls: type[Self],
        error: Any,
        severity: SeverityKind = SeverityKind.ERROR,
        payload: Any = None,
    ) -> Self:
        """
        Create a failure Result.

        Args:
            error: Exception describing the failure
            severity: Optional SeverityKind level (default: ERROR)
            payload: Optional structured metadata

        Returns:
            Result object with data=None
        """
        return cls(data=None, error=error, severity=severity, payload=payload)  # type: ignore
