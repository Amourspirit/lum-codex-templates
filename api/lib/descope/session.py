from typing import Any
from fastapi import HTTPException, Security, status

# from fastapi.security import HTTPAuthorizationCredentials
from ...lib.descope.auth import AUTH
from ...models.descope.descope_session import DescopeSession
from ..descope.client import DESCOPE_CLIENT


def get_descope_session(
    session_data: dict[str, Any] = Security(AUTH),
) -> DescopeSession:
    try:
        if not session_data:
            raise Exception("get_descope_session() No credentials provided.")
        print("get_descope_session() Session validated successfully.")
        return DescopeSession(session=session_data)
    except Exception:
        print("get_descope_session() Session validation failed.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session"
        )
