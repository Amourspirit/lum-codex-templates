from functools import wraps
from fastapi import Request, HTTPException
from typing import Callable, Optional, cast
from ..cache.session_handler import SessionHandler


def with_session(
    optional: bool = True,
    error_on_missing: bool = True,
) -> Callable[[Callable], Callable]:
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = cast(Request | None, kwargs.get("request"))

            if request is None:
                raise RuntimeError("with_session requires `request: Request` parameter")

            session_id: Optional[str] = None

            # 1. Header (non-GPT clients)
            session_id = request.headers.get("X-Session-ID")

            # 2. Query param (GPT-compatible)
            if not session_id:
                session_id = request.query_params.get("session_id")

            # 3. JSON body (POST routes)
            if not session_id:
                try:
                    body = await request.json()
                    if isinstance(body, dict):
                        session_id = body.get("session_id") or body.get(
                            "submission", {}
                        ).get("session_id")
                except Exception:
                    pass  # no body or not JSON

            # Enforce session requirement
            session_handler_instance = SessionHandler()
            if session_id:
                if error_on_missing and not session_handler_instance.has_session(
                    session_id
                ):
                    raise HTTPException(
                        status_code=404, detail="Session expired or not found"
                    )
                session = session_handler_instance.get_session(session_id)
                kwargs["session"] = session
                kwargs["session_id"] = session_id
            elif not optional:
                raise HTTPException(
                    status_code=400,
                    detail="session_id required (header, query, or body)",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
