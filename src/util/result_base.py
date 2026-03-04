from __future__ import annotations
from typing import Generic, TypeVar, Any, Optional, Type
from loguru import logger
from .severity_kind import SeverityKind

T = TypeVar("T")  # success type
E = TypeVar("E", bound=BaseException | None)  # error type
Self = TypeVar("Self", bound="ResultBase[Any, Any]")


class ResultBase(Generic[T, E]):
    """
    Core, domain-agnostic Result type.
    Never instantiate directly; use domain subclasses.
    Ensures: success => data != None, error=None / failure => data=None, error != None
    """

    def __init__(
        self,
        data: T = None,
        error: E = None,
        severity: SeverityKind | None = None,
        payload: Any = None,
    ) -> None:
        self._data: T = data
        self._error: E = error
        self._severity = severity
        self._payload = payload

        if self.data is not None and self.error is not None:
            logger.warning("Invalid Result state: data AND error set.")

    # -------------------------------------------------------
    # Constructors (Self-type ensures subclasses return themselves)
    # -------------------------------------------------------

    @classmethod
    def success(
        cls: Type[Self],
        data: T,
        severity: SeverityKind = SeverityKind.INFO,
        payload: Any = None,
    ) -> Self:
        return cls(data=data, error=None, severity=severity, payload=payload)

    @classmethod
    def failure(
        cls: Type[Self],
        error: Any,
        severity: SeverityKind = SeverityKind.ERROR,
        payload: Any = None,
    ) -> Self:
        return cls(data=None, error=error, severity=severity, payload=payload)

    # -------------------------------------------------------
    # State checks
    # -------------------------------------------------------

    def result_is_success(self) -> bool:
        """Return True if this Result represents success (error is None)."""
        return self.error is None

    def result_is_failure(self) -> bool:
        """Return True if this Result represents failure (error is not None)."""
        return self.error is not None

    def is_warning(self) -> bool:
        """Return True if this Result has severity WARNING."""
        return self.severity == SeverityKind.WARNING

    def is_error(self) -> bool:
        """Return True if this Result has severity ERROR."""
        return self.severity == SeverityKind.ERROR

    def is_critical(self) -> bool:
        """Return True if this Result has severity CRITICAL."""
        return self.severity == SeverityKind.CRITICAL

    # -------------------------------------------------------
    # Helpers
    # -------------------------------------------------------

    def unwrap(self) -> T:
        if self.error is not None:
            raise RuntimeError(f"unwrap() called on error result: {self.error}")
        return self.data  # type: ignore

    def expect(self, msg: str) -> T:
        if self.error is not None:
            raise RuntimeError(f"{msg}: {self.error}")
        return self.data  # type: ignore

    def __bool__(self) -> bool:
        return self.error is None

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(data={self.data!r}, "
            f"error={self.error!r}, severity={self.severity}, payload={self.payload!r})"
        )

    # region Properties
    @property
    def data(self) -> T:
        return self._data

    @property
    def error(self) -> E:
        return self._error

    @property
    def severity(self) -> Optional[SeverityKind]:
        return self._severity

    @severity.setter
    def severity(self, value: SeverityKind) -> None:
        self._severity = value

    @property
    def payload(self) -> Any:
        return self._payload

    @payload.setter
    def payload(self, value: Any) -> None:
        self._payload = value

    # endregion Properties
