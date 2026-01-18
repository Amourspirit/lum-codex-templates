import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Security
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi.security import HTTPAuthorizationCredentials
from api.routes.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src.config.pkg_config import PkgConfig

# if not os.getenv("RENDER_SERVICE_NAME"):
# only if not running on Render.com
from dotenv import load_dotenv

load_dotenv()  # reads variables from a .env file and sets them in os.environ

from api.lib.env import env_info  # noqa: E402
from api.routes import templates  # noqa: E402
from api.routes import executor_modes  # noqa: E402
from api.routes import privacy_terms  # noqa: E402
from api.routes.descope import route_protection  # noqa: E402
from api.lib.descope.auth import AUTH  # noqa: E402

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
async def docs_ui(credentials: HTTPAuthorizationCredentials = Security(AUTH)):
    return get_swagger_ui_html(
        openapi_url=f"{_FAST_API_CUSTOM_OPEN_API_PREFIX}/openapi.json", title="API Docs"
    )


@app.get(f"{_FAST_API_CUSTOM_OPEN_API_PREFIX}/redoc", include_in_schema=False)
async def redoc_ui(credentials: HTTPAuthorizationCredentials = Security(AUTH)):
    return get_redoc_html(
        openapi_url=f"{_FAST_API_CUSTOM_OPEN_API_PREFIX}/openapi.json", title="ReDoc"
    )
