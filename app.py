import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from api.routes.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# if not os.getenv("RENDER_SERVICE_NAME"):
# only if not running on Render.com
from dotenv import load_dotenv

load_dotenv()  # reads variables from a .env file and sets them in os.environ

from api.routes import templates
from api.routes import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load startup resources
    # https://fastapi.tiangolo.com/advanced/events/#async-context-manager
    FastAPICache.init(backend=InMemoryBackend())
    yield
    # Clean up resources if needed


app = FastAPI(title="Codex Templates", lifespan=lifespan)
app.include_router(templates.router)
app.include_router(auth.router)
app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore


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
