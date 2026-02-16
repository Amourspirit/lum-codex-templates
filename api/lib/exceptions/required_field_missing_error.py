from .verify_error import VerifyError


class RequiredFieldMissingError(VerifyError):
    """Custom exception for required field missing errors."""

    def __init__(self, message: str, field_name: str, errors: list[str] | str) -> None:
        super().__init__(message, field_name, errors)
