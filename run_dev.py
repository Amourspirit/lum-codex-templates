import os

os.environ["API_ENV_MODE"] = "dev"
from app import app as app

# run: uvicorn run_dev:app --reload
