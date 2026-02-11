import json
import os
import sys
from contextlib import asynccontextmanager
from loguru import logger
from contextvars import ContextVar
from starlette.responses import JSONResponse
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer
from starlette import status
from api.lib.exceptions import UnauthorizedException
from api.lib.env import env_info  # Must be early import to load env vars
from api.lib.descope.auth import AUTH
from descope.descope_client import DescopeClient
from api.lib.descope.auth_config import get_settings
from api.routes import executor_modes
from api.routes import privacy_terms
from api.routes import templates
from api.routes import well_known
from api.routes import auth_routes
from api.routes import doc_routes
from api.routes import prompts
from src.config.pkg_config import PkgConfig
from api.mcp.servers import templates_mcp


# from api.mcp.servers import echo_mcp
auth_settings = get_settings()

bearer_optional = HTTPBearer(auto_error=False)
auth_context_var: ContextVar[dict | None] = ContextVar("auth_context", default=None)

descope_client = DescopeClient(project_id=auth_settings.DESCOPE_PROJECT_ID)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    pkg_config = PkgConfig()
    # get the default schema
    openapi_schema = get_openapi(
        title=pkg_config.api_info.title,
        version=pkg_config.api_info.version,
        description=pkg_config.api_info.description,
        routes=app.routes,
    )
    # inject servers metadata
    servers = env_info.get_api_servers()
    if auth_settings.is_development:
        # add localhost server in dev mode
        port = int(os.getenv("PORT", 8000))
        servers.insert(0, {"url": f"http://localhost:{port}"})
    if servers:
        openapi_schema["servers"] = servers

    app.openapi_schema = openapi_schema
    return app.openapi_schema


mcp_templates = templates_mcp.init_mcp()

# ============================================================================
# Create the MCP HTTP app FIRST (needed for lifespan)
# ============================================================================
mcp_templates_app = mcp_templates.http_app(path="/mcp", transport="streamable-http")

# ============================================================================
# FastAPI Application with Combined Lifespan
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Combined lifespan handler that manages both FastAPI and FastMCP lifecycles.
    This is CRITICAL for Streamable HTTP transport to work properly.
    """

    # Initialize FastMCP's lifespan (required for Streamable HTTP)
    async with mcp_templates_app.lifespan(app):
        logger.remove()
        logger.add(sys.stderr, level=auth_settings.LOG_LEVEL)
        logger.info(
            "Application startup complete. Logging Level is set to {log_level}",
            log_level=auth_settings.LOG_LEVEL,
        )
        yield

    logger.info("👋 Shutting down...")


# Create a combined lifespan to manage the MCP session manager
app = FastAPI(
    title="Codex Templates",
    openapi_url=None,  # where schema is served
    docs_url=None,  # Swagger UI path
    redoc_url=None,  # ReDoc path
    lifespan=lifespan,
)

# ============================================================================
# CORS Middleware - Required for MCP Inspector
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your actual origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


app.include_router(templates.router)
app.include_router(executor_modes.router)
app.include_router(privacy_terms.router)
app.include_router(well_known.router)  # Include the .well-known endpoints
app.include_router(prompts.router)  # Include the prompts endpoints
app.include_router(
    auth_routes.router
)  # Include authentication routes (login/logout/callback)
if auth_settings.is_development:
    from api.routes import env_check

    app.include_router(env_check.router)  # Include env_check route only in development
    from api.routes import bruno_proxy

    app.include_router(
        bruno_proxy.router
    )  # Include Bruno MCP proxy route only in development
# app.include_router(login.router)
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore
app.openapi = custom_openapi  # override OpenAPI generator

doc_routes.register_doc_routes(
    app
)  # Register custom doc routes (OpenAPI, Swagger UI, ReDoc)


# ============================================================================
# Authentication Middleware for MCP Endpoint
# ============================================================================


@app.middleware("http")
async def mcp_auth_middleware(request: Request, call_next):
    """Middleware to validate Descope tokens for MCP endpoint requests."""
    # Reset context for this request
    token_data = auth_context_var.set(None)
    logger.debug(
        "mcp_auth_middleware() Start processing request: {path}", path=request.url.path
    )

    prefixes = [
        "/ping",
        "/.well-known/oauth-protected-resource",
        "/.well-known/",
    ]
    if auth_settings.is_development:
        prefixes.append("/env_check")
        prefixes.append("/bruno/tools/call")
        prefixes.append("/bruno/tools/call/markdown")

    allow_path_prefixes = tuple(prefixes)  # Convert to tuple for startswith() check

    if request.url.path == ("/"):
        logger.debug("mcp_auth_middleware() Skipping auth root path")
        return await call_next(request)

    if request.url.path.startswith(allow_path_prefixes):
        logger.debug(
            "mcp_auth_middleware() Skipping auth for path: {path}",
            path=request.url.path,
        )
        return await call_next(request)

    if request.url.path.startswith("/templates/mcp"):
        logger.debug("mcp_auth_middleware() Processing MCP request")
        authorization = request.headers.get("authorization")

        if authorization:
            parts = authorization.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
                request_body = await request.body()

                # Parse JSON from bytes
                try:
                    request_data = json.loads(request_body.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    request_data = {}

                is_tool_call = request_data.get("method") == "tools/call"

                required_scopes = None
                if is_tool_call:
                    logger.debug(
                        "mcp_auth_middleware() Detected tool call in MCP request"
                    )
                    scopes = env_info.get_api_scopes()
                    required_scopes = list(
                        scopes.read_scopes | scopes.write_scopes
                    )  # get required scope for your tool
                    logger.debug(
                        "mcp_auth_middleware() Required at least one scope for tool call: {scopes}",
                        scopes=required_scopes,
                    )

                try:
                    session = await AUTH.verify_token(token)
                    if required_scopes:
                        if not session.validate_scopes(required_scopes, match_any=True):
                            logger.debug(
                                "mcp_auth_middleware() Insufficient scopes: {scopes}",
                                scopes=session.scopes,
                            )
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail="Insufficient scopes for the requested resource",
                            )
                        auth_context_var.set(
                            {
                                "user_id": session.user_id,
                                "claims": session.session,
                            }
                        )
                except UnauthorizedException:
                    logger.debug("mcp_auth_middleware() Invalid or expired token")
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Invalid or expired token"},
                        # headers={"WWW-Authenticate": "Bearer"},
                        headers={
                            "WWW-Authenticate": f'Bearer realm="OAuth", resource_metadata="{auth_settings.BASE_URL}/.well-known/oauth-protected-resource"'
                        },
                    )
                except Exception as e:
                    logger.error("Token validation error: {error}", error=e)
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token validation failed",
                    )
        else:
            logger.debug(
                "mcp_auth_middleware() No Authorization header provided for MCP request"
            )
            auth_context_var.reset(token_data)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "No Authorization header provided for MCP request"},
                # headers={"WWW-Authenticate": "Bearer"},
                headers={
                    "WWW-Authenticate": f'Bearer realm="OAuth", resource_metadata="{auth_settings.BASE_URL}/.well-known/oauth-protected-resource"'
                },
            )

    response = await call_next(request)
    return response


# ============================================================================
# Mount FastMCP to FastAPI
# ============================================================================

app.mount("/templates", mcp_templates_app)


# Public route
@app.get("/", operation_id="root")
async def root():
    """Public root endpoint."""
    return {"message": "Welcome! Please /login to access the API documentation."}


@app.get("/ping", operation_id="ping")
async def ping():
    """Handle ping health checks and return a JSON payload acknowledging the request."""

    return {"msg": "pong"}


# ============================================================================
# Error Handlers
# ============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


if __name__ == "__main__":
    if os.getenv("LOCAL_DEV_MODE", "false").lower() == "true":
        import uvicorn

        port = int(
            os.getenv("PORT", 8000)
        )  # Use env PORT for deployment (e.g., Render.com)
        uvicorn.run(app, host="localhost", port=port)
        # uvicorn.run(mcp_app, host="localhost", port=8001)
