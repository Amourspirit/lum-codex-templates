import os

os.environ["API_ENV_MODE"] = "dev"


# app must be imported from main even if not used directly here.
# mcp looks for app in this module.
from main import app, mcp

if __name__ == "__main__":
    pass

# run: uvicorn run_dev:app --reload
