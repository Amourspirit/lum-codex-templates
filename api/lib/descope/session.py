from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials
from ...lib.descope.auth import AUTH
from ...models.descope.descope_session import DescopeSession
from ..descope.client import DESCOPE_CLIENT


def get_descope_session(
    credentials: HTTPAuthorizationCredentials = Security(AUTH),
) -> DescopeSession:
    try:
        print("get_descope_session() Validating session with token:")
        session = DESCOPE_CLIENT.validate_session(session_token=credentials.credentials)
        print("get_descope_session() Session validated successfully.")
        return DescopeSession(session=session)
    except Exception:
        print("get_descope_session() Session validation failed.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session"
        )
