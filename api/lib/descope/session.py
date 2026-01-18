from descope.descope_client import DescopeClient
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials
from ...lib.descope.auth import TokenVerifier
from ...models.descope.descope_session import DescopeSession
from ..descope.client import DESCOPE_CLIENT

auth = TokenVerifier()


def get_descope_session(
    credentials: HTTPAuthorizationCredentials = Security(auth),
) -> DescopeSession:
    try:
        session = DESCOPE_CLIENT.validate_session(session_token=credentials.credentials)
        return DescopeSession(session=session)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session")
