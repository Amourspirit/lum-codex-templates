import os
import sys
import urllib.parse
import secrets
from contextlib import asynccontextmanager
from loguru import logger

# import httpx
from fastapi import Depends, FastAPI, Request, Security
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from api.lib.env import env_info  # Must be early import to load env vars
from api.lib.descope.auth import TokenVerifier, AUTH
from api.lib.descope.auth_config import get_settings
from api.lib.exceptions import UnauthenticatedException
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


def _get_host_port(request: Request) -> tuple[str, int]:
    server = request.scope.get("server")
    if not server:
        raise ValueError("Server information not found in request scope")
    host, port = server
    return host, port


def _get_docs_url(request: Request) -> str:
    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}{_FAST_API_CUSTOM_OPEN_API_PREFIX}/docs"


def _get_descope_url(request: Request) -> str:
    docs_url = _get_docs_url(request)
    url = (
        f"{env_info.DESCOPE_LOGIN_BASE_URL}/{_FAST_API_CUSTOM_OPEN_API_PREFIX}{env_info.DESCOPE_PROJECT_ID}"
        f"?redirect_uri={docs_url}"
    )
    return url


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


def _require_login_or_redirect2(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_optional),
):
    def get_redirect_response(url: str) -> RedirectResponse:
        auth_url = (
            f"https://auth.descope.io/{env_info.DESCOPE_PROJECT_ID}"
            f"?flow=sign-codex_templates-redirect"
            f"&redirectUrl={url}"
        )
        print(f"Redirecting to Descope URL: {auth_url}")
        return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)

    base_url = str(request.base_url).rstrip("/")
    redirect_url = f"{base_url}{_FAST_API_CUSTOM_OPEN_API_PREFIX}/callback"
    encoded_redirect = urllib.parse.quote(redirect_url, safe="")

    # No Authorization header -> redirect to Descope login flow
    if creds is None:
        return get_redirect_response(encoded_redirect)

    # Validate token with your existing Descope validator (AUTH)
    try:
        # If your AUTH is a callable / dependency, adjust accordingly.
        # The idea: validate token and return payload/claims.
        payload = TokenVerifier()
        return payload
    except UnauthenticatedException:
        return get_redirect_response(encoded_redirect)


def custom_openapi():
    if api.openapi_schema:
        return api.openapi_schema
    config = PkgConfig()
    # get the default schema
    openapi_schema = get_openapi(
        title=config.api_info.title,
        version=config.api_info.version,
        description=config.api_info.description,
        routes=api.routes,
    )
    # inject servers metadata
    servers = env_info.get_api_servers()
    if env_info.API_ENV_MODE == "dev":
        # add localhost server in dev mode
        servers.insert(0, {"url": "http://localhost:8000"})
    if servers:
        openapi_schema["servers"] = servers

    api.openapi_schema = openapi_schema
    return api.openapi_schema


# auth = TokenVerifier()
_SETTINGS = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load startup resources
    # https://fastapi.tiangolo.com/advanced/events/#async-context-manager
    FastAPICache.init(backend=InMemoryBackend())
    yield
    # Clean up resources if needed


api = FastAPI()


api.include_router(templates.router)
api.include_router(executor_modes.router)
api.include_router(privacy_terms.router)
api.include_router(route_protection.router)
# app.include_router(login.router)
# app.state.limiter = limiter

api.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore


api.openapi = custom_openapi  # override OpenAPI generator

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@api.get("/ping", operation_id="ping")
async def ping():
    """Handle ping health checks and return a JSON payload acknowledging the request."""

    return {"msg": "pong"}


@api.get("/env_check/{env_var}", operation_id="env_check")
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


@api.get(
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

    return get_openapi(title="Your API", version="1.0.0", routes=api.routes)


@api.get(
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


@api.get(
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


# Public route
@api.get("/", operation_id="root")
async def root():
    """Public root endpoint."""
    return {"message": "Welcome! Please login to access the API documentation."}


# mcp = FastMCP(name="Codex Templates MCP Server")
mcp_templates = templates_mcp.init_mcp()
mcp_templates_app = mcp_templates.http_app(path="/mcp", transport="http")
# mcp_echo_app = echo_mcp.mcp.http_app(path="", transport="http")


@asynccontextmanager
async def global_lifespan(app: FastAPI):
    async with lifespan(app):
        async with mcp_templates_app.lifespan(app):
            # async with mcp_echo_app.lifespan(app):
            #     yield
            logger.remove()
            logger.add(sys.stderr, level=_SETTINGS.LOG_LEVEL)
            logger.info(
                "Application startup complete. Logging Level is set to {log_level}",
                log_level=_SETTINGS.LOG_LEVEL,
            )
            yield
            # Clean up resources if needed


app = FastAPI(
    title="Codex Templates",
    openapi_url=_OPEN_URL,  # where schema is served
    docs_url=_DOCS_URL,  # Swagger UI path
    redoc_url=_REDOC_URL,  # ReDoc path
    routes=api.routes,  # + mcp_templates_app.routes,
    # routes=api.routes,
    lifespan=global_lifespan,
)

app.mount("/templates", mcp_templates_app)  # /templates/mcp
# app.mount("/echo", mcp_echo_app)  # /echo/mcp


# @app.route("/.well-known/oauth-protected-resource", methods=["GET", "OPTIONS"])
# async def oauth_metadata(request: StarletteRequest) -> JSONResponse:
#     base_url = str(request.base_url).rstrip("/")
#     # Normalize to localhost in local dev mode to match MCP Inspector expectations
#     if os.getenv("LOCAL_DEV_MODE", "false").lower() == "true":
#         base_url = base_url.replace("127.0.0.1", "localhost")

#     return JSONResponse(
#         {
#             "resource": base_url,
#             "authorization_servers": [_SETTINGS.authorization_endpoint],
#             "scopes_supported": [
#                 "openid",
#                 "email",
#                 "profile",
#                 "login_access",
#                 "api.context:read",
#                 "mcp.template:read",
#             ],
#             "bearer_methods_supported": ["header", "body"],
#         }
#     )


if __name__ == "__main__":
    if os.getenv("LOCAL_DEV_MODE", "false").lower() == "true":
        import uvicorn

        port = int(
            os.getenv("PORT", 8000)
        )  # Use env PORT for deployment (e.g., Render.com)
        uvicorn.run(app, host="localhost", port=port)
        # uvicorn.run(mcp_app, host="localhost", port=8001)
