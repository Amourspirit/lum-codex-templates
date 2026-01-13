from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Request, Response
from ..lib.cache.session_handler import SessionHandler
from ..routes.limiter import limiter
from ..routes.auth import get_current_active_principle
from ..lib.decorators.session_decorator import with_session

router = APIRouter(prefix="/api/v1/session", tags=["session"])


@router.get("/start")
@limiter.limit("15/minute")
@with_session(optional=True, error_on_missing=False)
async def start_session(
    request: Request,
    response: Response,
    session: Optional[dict] = None,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
    x_session_id: str = Header(default=None, alias="X-Session-ID"),
):
    if session:
        response.headers["X-Session-ID"] = session["session_id"]
        return {
            "session_id": session["session_id"],
            "new_session": False,
            "message": "Session already exists",
            "expires_in_seconds": SessionHandler().ttl.total_seconds(),
        }
    session_handler = SessionHandler()

    # session_handler.get_session(x_session_id)
    session_id = session_handler.create_session()
    response.headers["X-Session-ID"] = session_id
    return {
        "session_id": session_id,
        "new_session": True,
        "message": "New session created",
        "expires_in_seconds": session_handler.ttl.total_seconds(),
    }


@router.get("/check")
@limiter.limit("15/minute")
@with_session()
async def check_session(
    request: Request,
    response: Response,
    session: Optional[dict] = None,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
    x_session_id: str = Header(default=None, alias="X-Session-ID"),
):
    if not session:
        raise HTTPException(status_code=404, detail="Session expired or not found")
    response.headers["X-Session-ID"] = session["session_id"]
    return session
