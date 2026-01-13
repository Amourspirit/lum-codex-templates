from functools import wraps
from os import error
from fastapi import Request, HTTPException
from typing import Callable
from starlette.requests import Request as StarletteRequest
from ..cache.session_handler import SessionHandler  # singleton


def with_session(
    optional: bool = True,
    error_on_missing: bool = True,
) -> Callable[[Callable], Callable]:
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, request: Request | StarletteRequest, **kwargs):
            # 🌀 1. Try to get session from header
            session_id = request.headers.get("X-Session-ID")

            # 🌀 2. Fall back to query param if header not found
            if not session_id:
                session_id = request.query_params.get("session_id")

            # 🧪 3. Handle session validation
            if session_id:
                if error_on_missing and not SessionHandler().has_session(session_id):
                    raise HTTPException(
                        status_code=404, detail="Session expired or not found"
                    )
                session = SessionHandler().get_session(session_id)
                # if not session:
                #     raise HTTPException(
                #         status_code=404, detail="Session expired or not found"
                #     )
                kwargs["session"] = session
            elif not optional:
                raise HTTPException(
                    status_code=400,
                    detail="Session ID required (header or query param)",
                )

            return await func(*args, request=request, **kwargs)

        return wrapper

    return decorator
