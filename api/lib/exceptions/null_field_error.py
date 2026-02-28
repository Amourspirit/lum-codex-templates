from .verify_error import VerifyError


class NullFieldError(VerifyError):
    """Custom exception for when a field is null or empty but is not allowed to be."""

    def __init__(self, message: str, field_name: str, errors: list[str] | str) -> None:
        super().__init__(message, field_name, errors)
