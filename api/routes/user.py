from typing import TYPE_CHECKING, Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Request, Response
from ..routes.limiter import limiter
from ..lib.decorators.session_decorator import with_session
from ..lib.env import env_info
from ..models.session.session import Session

if TYPE_CHECKING:
    from . import auth1 as auth
else:
    if env_info.AUTH_VERSION == 2:
        from . import auth2 as auth
    else:
        from . import auth1 as auth

router = APIRouter(prefix="/api/v1/user", tags=["user"])


@router.get("/whoami/{username}")
@limiter.limit("15/minute")
@with_session(optional=False)
async def check_session(
    username: str,
    request: Request,
    response: Response,
    session: Optional[Session] = None,
    current_principle: dict[str, str] = Depends(auth.get_current_active_principle),
    x_session_id: str = Header(default=None, alias="X-Session-ID"),
):
    if not session:
        raise HTTPException(status_code=404, detail="Session expired or not found")
    response.headers["X-Session-ID"] = session.session_id
    session_user = session.data.get("username", "anonymous")
    if session_user != username:
        session.data["username"] = username
    return session
