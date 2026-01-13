from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Request, Response
from ..routes.limiter import limiter
from ..routes.auth import get_current_active_principle
from ..lib.decorators.session_decorator import with_session

router = APIRouter(prefix="/api/v1/user", tags=["user"])


@router.get("/whoami/{username}")
@limiter.limit("15/minute")
@with_session(optional=False)
async def check_session(
    username: str,
    request: Request,
    response: Response,
    session: Optional[dict] = None,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
    x_session_id: str = Header(default=None, alias="X-Session-ID"),
):
    if not session:
        raise HTTPException(status_code=404, detail="Session expired or not found")
    response.headers["X-Session-ID"] = session["session_id"]
    session_user = session["data"].get("username", "anonymous")
    if session_user != username:
        session["data"]["username"] = username
    return session
