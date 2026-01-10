FROM python:3.13-slim

# 1. Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 2. Install dependencies (Cached Layer)
# We only bind the config files here so dependencies don't re-install 
# every time you change a line of code in the /api folder.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-install-project --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# 3. Copy the 'api' folder (and other necessary files)
# Syntax: COPY <source_on_host> <destination_in_container>
COPY ./api /app/api
COPY ./src /app/src
copy ./Assets /app/Assets
copy ./Metadata /app/Metadata
COPY ./app.py ./.env ./pyproject.toml ./uv.lock ./README.md /app/ 

# 4. Final sync to install the local project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Start the server (pointing to the module inside the api folder)
# Assuming main.py is inside the api folder
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]