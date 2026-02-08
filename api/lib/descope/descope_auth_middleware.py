import json
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from descope.descope_client import DescopeClient
from . import auth

# from fastapi.security import HTTPBearer
from .auth_config import get_settings


_SETTINGS = get_settings()
descope_client = DescopeClient(project_id=_SETTINGS.DESCOPE_PROJECT_ID)


# 3. Define the Auth Middleware
class DescopeAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/.well-known/"):
            return await call_next(request)

        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401, detail="Missing or invalid authorization header"
                )

            token = auth_header.split(" ")[1]

            request_body = await request.body()

            # Parse JSON from bytes
            try:
                request_data = json.loads(request_body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                request_data = {}

            is_tool_call = request_data.get("method") == "tools/call"

            required_scopes = []
            if is_tool_call:
                required_scopes = [
                    "mcp:template:read",
                    "api:context:read",
                ]  # get required scope for your tool
                # validation_options.required_scopes = required_scopes

            try:
                session = await auth.AUTH.verify_token(token)
                if required_scopes:
                    if not session.validate_scopes(required_scopes, match_any=True):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Insufficient scopes for the requested resource",
                        )

            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token validation failed",
                )

        except HTTPException as e:
            # resource_metadata=
            # This is  oauth-protected-resource such as `/.well-known/oauth-protected-resource/mcp`
            base_url = str(request.base_url).rstrip("/")
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": "unauthorized"
                    if e.status_code == status.HTTP_401_UNAUTHORIZED
                    else "forbidden",
                    "error_description": e.detail,
                },
                headers={
                    "WWW-Authenticate": f'Bearer realm="OAuth", resource_metadata="{base_url}/.well-known/oauth-protected-resource/mcp"'
                },
            )

        return await call_next(request)
