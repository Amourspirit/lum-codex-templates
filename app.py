import os
import urllib.parse
import secrets
from contextlib import asynccontextmanager
import httpx
from fastapi import Depends, FastAPI, Request, Security
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import HttpUrl
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
from fastapi_mcp import AuthConfig
from fastapi_mcp import FastApiMCP
from src.config.pkg_config import PkgConfig
from api.lib.descope.auth_config import get_settings

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

auth_settings = get_settings()
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
    if app.openapi_schema:
        return app.openapi_schema
    config = PkgConfig()
    # get the default schema
    openapi_schema = get_openapi(
        title=config.api_info.title,
        version=config.api_info.version,
        description=config.api_info.description,
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
config = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load startup resources
    # https://fastapi.tiangolo.com/advanced/events/#async-context-manager
    FastAPICache.init(backend=InMemoryBackend())
    yield
    # Clean up resources if needed


app = FastAPI(
    title="Codex Templates",
    lifespan=lifespan,
    openapi_url=_OPEN_URL,  # where schema is served
    docs_url=_DOCS_URL,  # Swagger UI path
    redoc_url=_REDOC_URL,  # ReDoc path
)


app.include_router(templates.router)
app.include_router(executor_modes.router)
app.include_router(privacy_terms.router)
app.include_router(route_protection.router)
# app.include_router(login.router)
# app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore


app.openapi = custom_openapi  # override OpenAPI generator

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/ping", operation_id="ping")
async def ping(request: Request):
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
@app.get("/", operation_id="root")
async def root():
    """Public root endpoint."""
    return {"message": "Welcome! Please /login to access the API documentation."}


mcp = FastApiMCP(
    app,
    name="Codex Templates MCP Server",
    description="MCP Server for Applying, and updating Codex Templates.",
    describe_full_response_schema=True,
    describe_all_responses=True,
    http_client=httpx.AsyncClient(base_url=auth_settings.MCP_SERVER_URL, timeout=30),
    auth_config=AuthConfig(
        custom_oauth_metadata={
            "issuer": HttpUrl(config.issuer),
            "jwks_uri": HttpUrl(config.jwks_url),
            "authorization_endpoint": HttpUrl(config.authorization_endpoint),
            "response_types_supported": config.response_types_supported,
            "subject_types_supported": config.subject_types_supported,
            "id_token_signing_alg_values_supported": config.id_token_signing_alg_values_supported,
            "code_challenge_methods_supported": config.code_challenge_methods_supported,
            "token_endpoint": HttpUrl(config.token_endpoint),
            "userinfo_endpoint": HttpUrl(config.userinfo_endpoint),
            "scopes_supported": ["openid"],
            "claims_supported": [
                "iss",
                "aud",
                "iat",
                "exp",
                "sub",
                "name",
                "email",
                "email_verified",
                "phone_number",
                "phone_number_verified",
                "picture",
                "family_name",
                "given_name",
            ],
            "revocation_endpoint": HttpUrl(config.revocation_endpoint),
            "registration_endpoint": HttpUrl(config.registration_endpoint),
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "token_endpoint_auth_methods_supported": ["client_secret_post"],
            "end_session_endpoint": HttpUrl(config.end_session_endpoint),
        },
        dependencies=[Depends(AUTH)],
    ),
    include_operations=[
        "read_privacy_policy",
        "get_template_cbib",
        "get_canonical_executor_mode",
        "get_template",
        "get_template_instructions",
        "get_template_manifest",
        "get_template_registry",
        "get_template_status",
        "verify_artifact",
        "finalize_artifact",
        "upgrade_artifact",
    ],
)

mcp.setup_server()
mcp.mount()
