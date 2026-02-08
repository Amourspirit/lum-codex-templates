"""
FastAPI + FastMCP with Streamable HTTP Transport and Descope Authentication
Requirements:
    pip install fastapi>=0.128.2 fastmcp==2.14.5 descope uvicorn
"""

import os
from typing import Annotated
from contextlib import asynccontextmanager
from contextvars import ContextVar

from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from descope.descope_client import DescopeClient
from descope.exceptions import AuthException
from fastmcp import FastMCP, Context
from api.lib.descope.auth_config import get_settings

# ============================================================================
# Configuration
# ============================================================================
_SETTINGS = get_settings()
DESCOPE_PROJECT_ID = _SETTINGS.DESCOPE_PROJECT_ID
SERVER_URL = "http://localhost:8000"

# Initialize Descope client
descope_client = DescopeClient(project_id=DESCOPE_PROJECT_ID)

# ContextVar for thread-safe request context handling
auth_context_var: ContextVar[dict | None] = ContextVar("auth_context", default=None)

# ============================================================================
# Descope Authentication Dependency (For standard FastAPI routes)
# ============================================================================


async def validate_descope_token(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected: Bearer <token>",
        )

    token = parts[1]

    try:
        jwt_response = descope_client.validate_session(token)
        return {
            "user_id": jwt_response.get("sub"),
            "email": jwt_response.get("email"),
            "claims": jwt_response,
        }
    except AuthException as e:
        raise HTTPException(
            status_code=401, detail=f"Invalid or expired token: {str(e)}"
        )


AuthenticatedUser = Annotated[dict, Depends(validate_descope_token)]

# ============================================================================
# FastMCP Server Setup
# ============================================================================

mcp = FastMCP(
    name="Templates MCP Server",
    stateless_http=True,
)


@mcp.tool()
async def private_template(ctx: Context) -> str:
    """
    A protected MCP tool that requires Descope authentication.
    Returns a personalized message with the authenticated user's ID.
    """
    # Retrieve context safely from ContextVar or FastMCP context
    auth_context = getattr(ctx, "_auth_context", None) or auth_context_var.get()

    if not auth_context:
        # This fallback usually won't be reached if middleware enforces auth,
        # but it serves as a secondary guardrail.
        return "Error: Authentication required. Please provide a valid Descope token."

    user_id = auth_context.get("user_id", "unknown")
    email = auth_context.get("email", "")

    message = f"Access granted to user: {user_id}"
    if email:
        message += f" ({email})"

    return message


@mcp.tool()
async def list_templates() -> list[str]:
    """Public tool that lists available templates."""
    return ["welcome-email", "password-reset", "newsletter", "invoice"]


@mcp.tool()
async def get_template(template_name: str) -> dict:
    """Retrieve a specific template by name."""
    templates = {
        "welcome-email": {
            "name": "welcome-email",
            "subject": "Welcome to Our Service!",
            "body": "Hello {{name}}, welcome aboard!",
        },
        "password-reset": {
            "name": "password-reset",
            "subject": "Password Reset Request",
            "body": "Click here to reset: {{reset_link}}",
        },
        "newsletter": {
            "name": "newsletter",
            "subject": "This Week's Updates",
            "body": "Here's what's new: {{content}}",
        },
        "invoice": {
            "name": "invoice",
            "subject": "Invoice #{{invoice_id}}",
            "body": "Amount due: {{amount}}",
        },
    }

    if template_name not in templates:
        return {"error": f"Template '{template_name}' not found"}

    return templates[template_name]


# ============================================================================
# Create the MCP HTTP app
# ============================================================================

mcp_templates_app = mcp.http_app(path="/mcp", transport="streamable-http")

# ============================================================================
# FastAPI Application with Combined Lifespan
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting FastAPI + FastMCP server...")
    print("📍 MCP endpoint: http://localhost:8000/templates/mcp")
    print(f"🔐 Descope Project ID: {DESCOPE_PROJECT_ID}")

    async with mcp_templates_app.lifespan(app):
        yield

    print("👋 Shutting down...")


app = FastAPI(
    title="Templates API with MCP",
    description="FastAPI application with FastMCP Streamable HTTP transport and Descope auth",
    version="1.0.0",
    lifespan=lifespan,
)

# ============================================================================
# CORS Middleware
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ============================================================================
# OAuth 2.0 Discovery Endpoints
# ============================================================================


@app.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource():
    """
    OAuth 2.0 Protected Resource Metadata (RFC 8707).
    Tells the client where to find the authorization server for this resource.
    """
    return {
        "resource": SERVER_URL,
        # Point to self if serving metadata, or Descope directly
        "authorization_servers": [SERVER_URL],
        "bearer_methods_supported": ["header"],
        "scopes_supported": ["openid", "profile", "email"],
    }


@app.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server():
    """
    OAuth 2.0 Authorization Server Metadata (RFC 8414).
    Maps the auth endpoints to Descope.
    """
    descope_base = f"https://api.descope.com/{DESCOPE_PROJECT_ID}"
    return {
        "issuer": descope_base,
        "authorization_endpoint": f"{descope_base}/oauth2/v1/authorize",
        "token_endpoint": f"{descope_base}/oauth2/v1/token",
        "jwks_uri": f"{descope_base}/.well-known/jwks.json",
        "response_types_supported": ["code", "token"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
        ],
        "scopes_supported": ["openid", "profile", "email"],
    }


# ============================================================================
# Authentication Middleware for MCP Endpoint (CRITICAL FIX)
# ============================================================================


@app.middleware("http")
async def mcp_auth_middleware(request: Request, call_next):
    """
    Middleware to validate Descope tokens for MCP endpoint requests.
    RETURNS 401 IF UNAUTHENTICATED to trigger client auth flow.
    """
    # Reset context for this request
    token_data = auth_context_var.set(None)

    if request.url.path.startswith("/templates/mcp"):
        authorization = request.headers.get("authorization")

        # 1. Check for Authorization Header
        if not authorization:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 2. Parse Bearer Token
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid Authorization header format"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = parts[1]

        # 3. Validate Token with Descope
        try:
            jwt_response = descope_client.validate_session(token)
            auth_context_var.set(
                {
                    "user_id": jwt_response.get("sub"),
                    "email": jwt_response.get("email"),
                    "claims": jwt_response,
                }
            )
        except AuthException:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
                # headers={"WWW-Authenticate": "Bearer"},
                headers={
                    "WWW-Authenticate": f'Bearer realm="OAuth", resource_metadata="{SERVER_URL}/.well-known/oauth-protected-resource"'
                },
            )

    try:
        response = await call_next(request)
        return response
    finally:
        # Clean up context var (optional but good practice)
        auth_context_var.reset(token_data)


# ============================================================================
# Mount FastMCP to FastAPI
# ============================================================================

app.mount("/templates", mcp_templates_app)

# ============================================================================
# FastAPI Routes
# ============================================================================


@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "Templates API with MCP",
        "mcp_endpoint": "/templates/mcp/sse",  # Hint for users
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("sample:app", host="0.0.0.0", port=8000, reload=True)
