import json
import os
import sys
import urllib.parse
import secrets
from contextlib import asynccontextmanager
from loguru import logger

# import httpx
from contextvars import ContextVar
from starlette.responses import JSONResponse
from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status
from api.lib.exceptions import UnauthenticatedException, UnauthorizedException
from api.lib.env import env_info  # Must be early import to load env vars
from api.lib.descope.auth import TokenVerifier, AUTH
from api.lib.descope.auth_config import get_settings
from api.routes import executor_modes
from api.routes import privacy_terms
from api.routes import templates
from api.routes.descope import route_protection
from src.config.pkg_config import PkgConfig
from api.mcp.servers import templates_mcp

# from api.mcp.servers import echo_mcp


if env_info.API_ENV_MODE == "prod":
    _FAST_API_CUSTOM_OPEN_API_PREFIX = ""
    _OPEN_URL = None  # where schema is served
    _DOCS_URL = None  # Swagger UI path
    _REDOC_URL = None  # ReDoc path
else:
    _FAST_API_CUSTOM_OPEN_API_PREFIX = "/api/v1"
    _OPEN_URL = "/openapi.json"  # where schema is served
    _DOCS_URL = "/docs"  # Swagger UI path
    _REDOC_URL = "/redoc"  # ReDoc path

bearer_optional = HTTPBearer(auto_error=False)
auth_context_var: ContextVar[dict | None] = ContextVar("auth_context", default=None)


def _get_docs_url(request: Request) -> str:
    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}{_FAST_API_CUSTOM_OPEN_API_PREFIX}/docs"


def _require_login_or_redirect(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_optional),
):
    def get_redirect_response(url: str, state) -> RedirectResponse:
        params = {
            "response_type": "code",
            "client_id": env_info.DESCOPE_INBOUND_APP_CLIENT_ID,
            "redirect_uri": url,
            "scope": "openid",  # Required for OIDC
            "flow": "sign-codex_templates-redirect",  # The flow ID to run
            "state": state,
        }
        query_string = urllib.parse.urlencode(params)
        auth_url = f"https://api.descope.com/oauth2/v1/apps/authorize?{query_string}"

        return RedirectResponse(url=auth_url)

    state = secrets.token_urlsafe(16)
    # descope_url = _get_descope_url(request)
    docs_url = _get_docs_url(request)
    # No Authorization header -> redirect to Descope login flow
    if creds is None:
        return get_redirect_response(docs_url, state)

    # Validate token with your existing Descope validator (AUTH)
    try:
        # If your AUTH is a callable / dependency, adjust accordingly.
        # The idea: validate token and return payload/claims.
        payload = TokenVerifier()
        return payload
    except UnauthenticatedException:
        return get_redirect_response(docs_url, state)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    pkg_config = PkgConfig()
    # get the default schema
    openapi_schema = get_openapi(
        title=pkg_config.api_info.title,
        version=pkg_config.api_info.version,
        description=pkg_config.api_info.description,
        routes=app.routes,
    )
    # inject servers metadata
    servers = env_info.get_api_servers()
    if env_info.API_ENV_MODE == "dev":
        # add localhost server in dev mode
        servers.insert(0, {"url": "http://localhost:8000"})
    if servers:
        openapi_schema["servers"] = servers

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# auth = TokenVerifier()
_SETTINGS = get_settings()

mcp_templates = templates_mcp.init_mcp()

# ============================================================================
# Create the MCP HTTP app FIRST (needed for lifespan)
# ============================================================================
mcp_templates_app = mcp_templates.http_app(path="/mcp", transport="streamable-http")

# ============================================================================
# FastAPI Application with Combined Lifespan
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Combined lifespan handler that manages both FastAPI and FastMCP lifecycles.
    This is CRITICAL for Streamable HTTP transport to work properly.
    """

    # Initialize FastMCP's lifespan (required for Streamable HTTP)
    async with mcp_templates_app.lifespan(app):
        logger.remove()
        logger.add(sys.stderr, level=_SETTINGS.LOG_LEVEL)
        logger.info(
            "Application startup complete. Logging Level is set to {log_level}",
            log_level=_SETTINGS.LOG_LEVEL,
        )
        yield

    logger.info("👋 Shutting down...")


# Create a combined lifespan to manage the MCP session manager
app = FastAPI(
    title="Codex Templates",
    openapi_url=_OPEN_URL,  # where schema is served
    docs_url=_DOCS_URL,  # Swagger UI path
    redoc_url=_REDOC_URL,  # ReDoc path
    lifespan=lifespan,
)

# ============================================================================
# CORS Middleware - Required for MCP Inspector
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your actual origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


app.include_router(templates.router)
app.include_router(executor_modes.router)
app.include_router(privacy_terms.router)
app.include_router(route_protection.router)
# app.include_router(login.router)
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore
app.openapi = custom_openapi  # override OpenAPI generator

# OAuth 2.0 Discovery Endpoints (Required for MCP Inspector v0.19.0)
# ============================================================================


@app.get("/.well-known/oauth-protected-resource")
@app.get("/.well-known/oauth-protected-resource/{path:path}")
async def oauth_protected_resource(path: str = ""):
    """OAuth 2.0 Protected Resource Metadata (RFC 8707)."""
    return {
        "resource": _SETTINGS.BASE_URL,
        "authorization_servers": _SETTINGS.authorization_servers,
        "bearer_methods_supported": ["header"],
        "scopes_supported": ["openid", "profile", "email"],
    }


@app.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server():
    """OAuth 2.0 Authorization Server Metadata (RFC 8414)."""
    return {
        "issuer": _SETTINGS.issuer,
        "authorization_endpoint": _SETTINGS.authorization_endpoint,  # f"{descope_base}/oauth2/v1/authorize",
        "token_endpoint": _SETTINGS.token_endpoint,  # f"{descope_base}/oauth2/v1/token",
        "jwks_uri": _SETTINGS.jwks_url,  # f"{descope_base}/.well-known/jwks.json",
        "response_types_supported": _SETTINGS.response_types_supported,
        "grant_types_supported": _SETTINGS.grant_types_supported,
        "token_endpoint_auth_methods_supported": _SETTINGS.token_endpoint_auth_methods_supported,
        "scopes_supported": _SETTINGS.scopes_supported,
    }


@app.get("/.well-known/openid-configuration")
async def openid_configuration():
    """OpenID Connect Discovery endpoint."""
    return {
        "issuer": _SETTINGS.issuer,
        "authorization_endpoint": _SETTINGS.authorization_endpoint,
        "token_endpoint": _SETTINGS.token_endpoint,
        "userinfo_endpoint": _SETTINGS.userinfo_endpoint,
        "jwks_uri": _SETTINGS.jwks_url,
        "response_types_supported": _SETTINGS.response_types_supported,
        "subject_types_supported": _SETTINGS.subject_types_supported,
        "id_token_signing_alg_values_supported": _SETTINGS.id_token_signing_alg_values_supported,
        "scopes_supported": _SETTINGS.scopes_supported,
        "token_endpoint_auth_methods_supported": _SETTINGS.token_endpoint_auth_methods_supported,
        "claims_supported": _SETTINGS.claims_supported,
    }


# ============================================================================
# Authentication Middleware for MCP Endpoint
# ============================================================================


@app.middleware("http")
async def mcp_auth_middleware(request: Request, call_next):
    """Middleware to validate Descope tokens for MCP endpoint requests."""
    # Reset context for this request
    token_data = auth_context_var.set(None)

    if request.url.path.startswith("/.well-known/"):
        return await call_next(request)

    if request.url.path.startswith("/templates/mcp"):
        authorization = request.headers.get("authorization")

        if authorization:
            parts = authorization.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
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
                        "mcp.template:read",
                        "api.context:read",
                    ]  # get required scope for your tool

                try:
                    session = await AUTH.verify_token(token)
                    if required_scopes:
                        if not session.validate_scopes(required_scopes, match_any=True):
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail="Insufficient scopes for the requested resource",
                            )
                        auth_context_var.set(
                            {
                                "user_id": session.user_id,
                                "claims": session.session,
                            }
                        )
                except UnauthorizedException:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Invalid or expired token"},
                        # headers={"WWW-Authenticate": "Bearer"},
                        headers={
                            "WWW-Authenticate": f'Bearer realm="OAuth", resource_metadata="{_SETTINGS.BASE_URL}/.well-known/oauth-protected-resource"'
                        },
                    )
                except Exception:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token validation failed",
                    )
        else:
            auth_context_var.reset(token_data)

    response = await call_next(request)
    return response


# Protected /docs route

# @app.get("/docs", include_in_schema=False)
# async def custom_swagger_ui(user=Depends(login.get_current_user)):
#     """Serve Swagger UI only to authenticated users."""
#     return get_swagger_ui_html(
#         openapi_url="/openapi.json",
#         title=app.title + " - API Docs",
#     )


# Protected OpenAPI schema endpoint
# @app.get("/openapi.json", include_in_schema=False)
# async def openapi_schema(user=Depends(login.get_current_user)):
#     """Serve OpenAPI schema only to authenticated users."""
#     from fastapi.openapi.utils import get_openapi

#     return get_openapi(
#         title=app.title,
#         version=app.version,
#         routes=app.routes,
#     )


# Example protected route
# @app.get("/api/protected")
# async def protected_route(user=Depends(login.get_current_user)):
#     """Example protected endpoint."""
#     return {"message": "You are authenticated!", "user": user}


# ============================================================================
# Mount FastMCP to FastAPI
# ============================================================================

app.mount("/templates", mcp_templates_app)


# Public route
@app.get("/", operation_id="root")
async def root():
    """Public root endpoint."""
    return {"message": "Welcome! Please login to access the API documentation."}


@app.get("/ping", operation_id="ping")
async def ping():
    """Handle ping health checks and return a JSON payload acknowledging the request."""

    return {"msg": "pong"}


@app.get("/env_check/{env_var}", operation_id="env_check")
async def env_check(env_var: str, auth_result: str = Security(AUTH)):
    """Check whether a specified environment variable is set and report its status.
    Args:
        env_var: The name of the environment variable to inspect.
        request: The incoming HTTP request associated with the check.
    Returns:
        A dictionary containing the environment variable name, whether it is set,
        and, if applicable, the type of the stored value.
    """

    value = os.getenv(env_var, None)
    if value is None:
        return {"env_var": env_var, "value": "Not Set"}
    return {"env_var": env_var, "value": "Is Set", "type": str(type(value))}


@app.get(
    f"{_FAST_API_CUSTOM_OPEN_API_PREFIX}/openapi.json",
    include_in_schema=False,
    operation_id="openapi_schema",
)
async def openapi_schema(credentials: HTTPAuthorizationCredentials = Security(AUTH)):
    """Generate the OpenAPI schema for the application.
    Parameters
    ----------
    credentials : HTTPAuthorizationCredentials, optional
        Authorization credentials provided by the configured security dependency.
    Returns
    -------
    dict
        The OpenAPI specification describing the registered API routes.
    """

    return get_openapi(title="Your API", version="1.0.0", routes=app.routes)


@app.get(
    f"{_FAST_API_CUSTOM_OPEN_API_PREFIX}/docs",
    include_in_schema=False,
    operation_id="docs_ui",
)
async def docs_ui(user=Depends(_require_login_or_redirect)):
    """Render the Swagger UI for authenticated users or return a redirect response when authentication is required.
    Parameters
    ----------
    user : Any
        Result from the `_require_login_or_redirect` dependency, which may be a user object or a `RedirectResponse`.
    Returns
    -------
    HTMLResponse | RedirectResponse
        Swagger UI HTML response when authenticated, otherwise the redirect response.
    """

    if isinstance(user, RedirectResponse):
        return user
    return get_swagger_ui_html(
        openapi_url=f"{_FAST_API_CUSTOM_OPEN_API_PREFIX}/openapi.json", title="API Docs"
    )


@app.get(
    f"{_FAST_API_CUSTOM_OPEN_API_PREFIX}/redoc",
    include_in_schema=False,
    operation_id="redoc_ui",
)
async def redoc_ui(credentials: HTTPAuthorizationCredentials = Security(AUTH)):
    """
    Return the ReDoc HTML page for the OpenAPI schema, respecting custom prefix settings.
    Parameters
    ----------
    credentials : fastapi.security.HTTPAuthorizationCredentials
        Authorization credentials extracted via the configured security dependency.
    Returns
    -------
    str
        HTML markup generated by `fastapi.openapi.docs.get_redoc_html` for the configured OpenAPI endpoint.
    """

    return get_redoc_html(
        openapi_url=f"{_FAST_API_CUSTOM_OPEN_API_PREFIX}/openapi.json", title="ReDoc"
    )


# ============================================================================
# Error Handlers
# ============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


if __name__ == "__main__":
    if os.getenv("LOCAL_DEV_MODE", "false").lower() == "true":
        import uvicorn

        port = int(
            os.getenv("PORT", 8000)
        )  # Use env PORT for deployment (e.g., Render.com)
        uvicorn.run(app, host="localhost", port=port)
        # uvicorn.run(mcp_app, host="localhost", port=8001)
