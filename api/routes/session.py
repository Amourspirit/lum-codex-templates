from fastapi import APIRouter, HTTPException, Depends, Request
from ..lib.cache.session_handler import SessionHandler
from ..routes.limiter import limiter
from ..routes.auth import get_current_active_principle

router = APIRouter(prefix="/api/v1/session", tags=["session"])

session_handler = SessionHandler(ttl_seconds=14400)  # 4 hours default


@router.post("/start")
@limiter.limit("15/minute")
async def start_session(
    request: Request,
):
    session_id = session_handler.create_session()
    return {
        "session_id": session_id,
        "expires_in_seconds": session_handler.ttl.total_seconds(),
    }


@router.get("/{session_id}")
@limiter.limit("15/minute")
async def check_session(
    session_id: str,
    request: Request,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
):
    session = session_handler.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session expired or not found")
    return session
