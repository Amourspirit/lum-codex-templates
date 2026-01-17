import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING
from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from api.lib import env
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

from api.routes import session  # noqa: E402
from api.routes import user  # noqa: E402

if TYPE_CHECKING:
    from api.routes import auth1 as auth  # noqa: E402
else:
    if env_info.AUTH_VERSION == 1:
        from api.routes import auth1 as auth  # noqa: E402
    elif env_info.AUTH_VERSION == 2:
        from api.routes import auth2 as auth  # noqa: E402
    else:
        raise ImportError("Unsupported AUTH_VERSION in env_info")


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


app = FastAPI(title="Codex Templates", lifespan=lifespan)
app.include_router(templates.router)
app.include_router(executor_modes.router)
app.include_router(auth.router)
app.include_router(session.router)
app.include_router(user.router)
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
