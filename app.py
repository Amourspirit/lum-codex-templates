import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

if not os.getenv("RENDER_SERVICE_NAME"):
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


@app.get("/ping")
async def ping():
    return {"msg": "pong"}
