"""
FastAPI + FastMCP with Streamable HTTP Transport and Descope Authentication
Requirements:
    pip install fastapi>=0.128.2 fastmcp==2.14.5 descope uvicorn
"""

import os
from typing import Annotated
from contextlib import asynccontextmanager

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

# ============================================================================
# Descope Authentication Dependency
# ============================================================================


async def validate_descope_token(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    """
    FastAPI dependency that validates Descope JWT from Authorization header.
    Returns the validated token claims if successful.
    """
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

_request_auth_context: dict = {}


@mcp.tool()
async def private_template(ctx: Context) -> str:
    """
    A protected MCP tool that requires Descope authentication.
    Returns a personalized message with the authenticated user's ID.
    """
    auth_context = getattr(ctx, "_auth_context", None) or _request_auth_context.get(
        "current"
    )

    if not auth_context:
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
# Create the MCP HTTP app FIRST (needed for lifespan)
# ============================================================================

mcp_templates_app = mcp.http_app(path="/mcp", transport="streamable-http")

# ============================================================================
# FastAPI Application with Combined Lifespan
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Combined lifespan handler that manages both FastAPI and FastMCP lifecycles.
    This is CRITICAL for Streamable HTTP transport to work properly.
    """
    print("🚀 Starting FastAPI + FastMCP server...")
    print("📍 MCP endpoint: http://localhost:8000/templates/mcp")
    print(f"🔐 Descope Project ID: {DESCOPE_PROJECT_ID}")

    # Initialize FastMCP's lifespan (required for Streamable HTTP)
    async with mcp_templates_app.lifespan(app):
        yield

    print("👋 Shutting down...")


app = FastAPI(
    title="Templates API with MCP",
    description="FastAPI application with FastMCP Streamable HTTP transport and Descope auth",
    version="1.0.0",
    lifespan=lifespan,  # Use our combined lifespan handler
)

# ============================================================================
# CORS Middleware - Required for MCP Inspector
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
# OAuth 2.0 Discovery Endpoints (Required for MCP Inspector v0.19.0)
# ============================================================================


@app.get("/.well-known/oauth-protected-resource")
@app.get("/.well-known/oauth-protected-resource/{path:path}")
async def oauth_protected_resource(path: str = ""):
    """OAuth 2.0 Protected Resource Metadata (RFC 8707)."""
    return {
        "resource": SERVER_URL,
        "authorization_servers": [f"https://api.descope.com/{DESCOPE_PROJECT_ID}"],
        "bearer_methods_supported": ["header"],
        "scopes_supported": ["openid", "profile", "email"],
    }


@app.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server():
    """OAuth 2.0 Authorization Server Metadata (RFC 8414)."""
    # descope_base = f"https://api.descope.com/{DESCOPE_PROJECT_ID}"
    return {
        "issuer": _SETTINGS.issuer,
        "authorization_endpoint": _SETTINGS.authorization_endpoint,  # f"{descope_base}/oauth2/v1/authorize",
        "token_endpoint": _SETTINGS.token_endpoint,  # f"{descope_base}/oauth2/v1/token",
        "jwks_uri": _SETTINGS.jwks_url,  # f"{descope_base}/.well-known/jwks.json",
        "response_types_supported": ["code", "token"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
        ],
        "scopes_supported": ["openid", "profile", "email"],
    }


@app.get("/.well-known/openid-configuration")
async def openid_configuration():
    """OpenID Connect Discovery endpoint."""
    descope_base = f"https://api.descope.com/{DESCOPE_PROJECT_ID}"
    return {
        "issuer": descope_base,
        "authorization_endpoint": f"{descope_base}/oauth2/v1/authorize",
        "token_endpoint": f"{descope_base}/oauth2/v1/token",
        "userinfo_endpoint": f"{descope_base}/oauth2/v1/userinfo",
        "jwks_uri": f"{descope_base}/.well-known/jwks.json",
        "response_types_supported": ["code", "id_token", "token"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["openid", "profile", "email"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
        ],
        "claims_supported": ["sub", "email", "name", "picture"],
    }


# ============================================================================
# Authentication Middleware for MCP Endpoint
# ============================================================================


@app.middleware("http")
async def mcp_auth_middleware(request: Request, call_next):
    """Middleware to validate Descope tokens for MCP endpoint requests."""
    global _request_auth_context

    if request.url.path.startswith("/templates/mcp"):
        authorization = request.headers.get("authorization")

        if authorization:
            parts = authorization.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
                try:
                    jwt_response = descope_client.validate_session(token)
                    _request_auth_context["current"] = {
                        "user_id": jwt_response.get("sub"),
                        "email": jwt_response.get("email"),
                        "claims": jwt_response,
                    }
                except AuthException:
                    _request_auth_context["current"] = None
        else:
            _request_auth_context["current"] = None

    response = await call_next(request)
    return response


# ============================================================================
# Mount FastMCP to FastAPI
# ============================================================================

app.mount("/templates", mcp_templates_app)

# ============================================================================
# FastAPI Routes
# ============================================================================


@app.get("/")
async def root():
    """Health check and API info endpoint."""
    return {
        "status": "healthy",
        "service": "Templates API with MCP",
        "mcp_endpoint": "/templates/mcp",
        "docs": "/docs",
        "well_known": {
            "oauth_protected_resource": "/.well-known/oauth-protected-resource",
            "oauth_authorization_server": "/.well-known/oauth-authorization-server",
            "openid_configuration": "/.well-known/openid-configuration",
        },
    }


@app.get("/private")
async def private_route(user: AuthenticatedUser):
    """Protected route that requires a valid Descope session."""
    return {
        "message": "You have accessed a private route!",
        "user_id": user["user_id"],
        "email": user.get("email"),
        "authenticated": True,
    }


@app.get("/public")
async def public_route():
    """Public route - no authentication required."""
    return {"message": "This is a public endpoint", "authenticated": False}


# ============================================================================
# Error Handlers
# ============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("sample:app", host="0.0.0.0", port=8000, reload=True)
