from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials
from ...lib.descope.auth import AUTH
from ...models.descope.descope_session import DescopeSession
from ..descope.client import DESCOPE_CLIENT


def get_descope_session(
    credentials: HTTPAuthorizationCredentials = Security(AUTH),
) -> DescopeSession:
    try:
        session = DESCOPE_CLIENT.validate_session(session_token=credentials.credentials)
        return DescopeSession(session=session)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session")
