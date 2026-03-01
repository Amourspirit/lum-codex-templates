from .verify_error import VerifyError


class NullFieldError(VerifyError):
    """Custom exception for when a field is null or empty but is not allowed to be."""

    pass
