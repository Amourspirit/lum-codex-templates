# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.routes import templates
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache


from dotenv import load_dotenv

load_dotenv()  # reads variables from a .env file and sets them in os.environ


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load startup resources
    # https://fastapi.tiangolo.com/advanced/events/#async-context-manager
    FastAPICache.init(InMemoryBackend())
    yield
    # Clean up resources if needed


app = FastAPI(lifespan=lifespan)
app.include_router(templates.router)


@app.get("/ping")
async def ping():
    return {"msg": "pong"}
