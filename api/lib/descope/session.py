from fastapi import HTTPException, Request, status
from loguru import logger

from descope.descope_client import DescopeClient
from api.lib.descope.auth_config import get_settings
from api.models.descope.descope_session import DescopeSession

auth_settings = get_settings()
descope_client = DescopeClient(project_id=auth_settings.DESCOPE_PROJECT_ID)

# def get_descope_session(
#     request: Request, session_data: dict[str, Any] = Security(AUTH),
# ) -> DescopeSession:
#     try:
#         if not session_data:
#             raise Exception("get_descope_session() No credentials provided.")
#         logger.debug("get_descope_session() Session validated successfully.")
#         return DescopeSession(session=session_data)
#     except Exception as e:
#         logger.error(
#             "get_descope_session() Session validation failed: {error}", error=e
#         )
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session"
#         )


def get_user_session(request: Request) -> DescopeSession | None:
    """
    Checks if the user has a valid session/refresh token.
    Returns the user dict if valid, None otherwise.
    Does NOT raise exceptions.
    """

    def get_auth_header_token() -> str | None:
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            logger.debug("get_auth_header_token() No valid Authorization header found.")
            return None
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.debug("get_auth_header_token() Malformed Authorization header.")
            return None
        return parts[1]

    def get_cookie_token() -> str | None:
        access_token = request.cookies.get("access_token")
        if not access_token:
            logger.debug("get_cookie_token() No access_token cookie found.")
            return None
        logger.debug("get_cookie_token() access_token cookie found.")
        return access_token

    token = get_auth_header_token() or get_cookie_token()
    if not token:
        return None

    refresh_token = request.cookies.get("refresh_token")

    try:
        # Validate the token using Descope SDK
        if refresh_token:
            logger.debug("get_user_session() Validating session with refresh token")
            # Handles expired access tokens if refresh token is valid
            data = descope_client.validate_and_refresh_session(
                session_token=token, refresh_token=refresh_token
            )
        else:
            logger.debug("get_user_session() Validating session without refresh token")
            data = descope_client.validate_session(session_token=token)

        return DescopeSession(
            session=data, access_token=token, refresh_token=refresh_token
        )
    except Exception:
        # If any validation fails, return None so the caller knows they aren't logged in
        return None


def get_descope_session(request: Request) -> DescopeSession:
    """
    Dependency for protected routes.
    Uses the helper above, but raises 401 if it fails.
    """
    session = get_user_session(request)
    if not session:
        logger.debug("get_descope_session() No valid session found.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return session
