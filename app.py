import os
import urllib.parse
import secrets
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Security
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status
from api.lib.descope.exception_handlers import UnauthenticatedException
from api.routes.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src.config.pkg_config import PkgConfig
from descope.exceptions import AuthException

# if not os.getenv("RENDER_SERVICE_NAME"):
# only if not running on Render.com
from dotenv import load_dotenv

load_dotenv()  # reads variables from a .env file and sets them in os.environ

from api.lib.env import env_info  # noqa: E402
from api.routes import templates  # noqa: E402
from api.routes import executor_modes  # noqa: E402
from api.routes import privacy_terms  # noqa: E402
from api.routes.descope import route_protection  # noqa: E402
from api.routes.descope import login
from api.lib.descope.auth import TokenVerifier, AUTH  # noqa: E402
from api.lib.descope.client import DESCOPE_CLIENT  # noqa: E402

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
            "client_id": env_info.DESCOPE_PROJECT_ID,
            "redirect_uri": url,
            "scope": "openid",  # Required for OIDC
            "flow": "sign-codex_templates-redirect",  # The flow ID to run
            "state": state,
        }
        query_string = urllib.parse.urlencode(params)
        auth_url = f"https://api.descope.com/oauth2/v1/authorize?{query_string}"

        return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)

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
app.include_router(login.router)
app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore


app.openapi = custom_openapi  # override OpenAPI generator


@app.get("/ping")
@limiter.limit("15/minute")
async def ping(request: Request):
    return {"msg": "pong"}


@app.get("/env_check/{env_var}")
@limiter.limit("15/minute")
async def env_check(env_var: str, request: Request):
    value = os.getenv(env_var, None)
    if value is None:
        return {"env_var": env_var, "value": "Not Set"}
    return {"env_var": env_var, "value": "Is Set", "type": str(type(value))}


@app.get(f"{_FAST_API_CUSTOM_OPEN_API_PREFIX}/openapi.json", include_in_schema=False)
async def openapi_schema(credentials: HTTPAuthorizationCredentials = Security(AUTH)):
    return get_openapi(title="Your API", version="1.0.0", routes=app.routes)


@app.get(f"{_FAST_API_CUSTOM_OPEN_API_PREFIX}/docs", include_in_schema=False)
async def docs_ui(user=Depends(_require_login_or_redirect)):
    if isinstance(user, RedirectResponse):
        return user
    return get_swagger_ui_html(
        openapi_url=f"{_FAST_API_CUSTOM_OPEN_API_PREFIX}/openapi.json", title="API Docs"
    )


@app.get(f"{_FAST_API_CUSTOM_OPEN_API_PREFIX}/redoc", include_in_schema=False)
async def redoc_ui(credentials: HTTPAuthorizationCredentials = Security(AUTH)):
    return get_redoc_html(
        openapi_url=f"{_FAST_API_CUSTOM_OPEN_API_PREFIX}/openapi.json", title="ReDoc"
    )
