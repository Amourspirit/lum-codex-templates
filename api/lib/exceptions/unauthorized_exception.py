from fastapi import status, HTTPException


class UnauthorizedException(HTTPException):
    """Raised when an authenticated user lacks necessary permissions."""

    def __init__(self, detail: str = "You are not authorized to access this resource"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
