# main.py
from fastapi import FastAPI
from api.routes import templates


app = FastAPI()
app.include_router(templates.router)


@app.get("/ping")
def ping():
    return {"msg": "pong"}
