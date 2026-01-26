from typing import Any
from fastapi import HTTPException, Security, status
from loguru import logger

# from fastapi.security import HTTPAuthorizationCredentials
from ...lib.descope.auth import AUTH
from ...models.descope.descope_session import DescopeSession


def get_descope_session(
    session_data: dict[str, Any] = Security(AUTH),
) -> DescopeSession:
    try:
        if not session_data:
            raise Exception("get_descope_session() No credentials provided.")
        logger.debug("get_descope_session() Session validated successfully.")
        return DescopeSession(session=session_data)
    except Exception as e:
        logger.error(
            "get_descope_session() Session validation failed: {error}", error=e
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session"
        )
