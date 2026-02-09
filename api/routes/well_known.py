from fastapi import APIRouter
from api.lib.descope.auth_config import get_settings

_AUTH_SETTINGS = get_settings()

router = APIRouter(tags=["Authorization", "Authentication"])

# OAuth 2.0 Discovery Endpoints (Required for MCP Inspector v0.19.0)
# ============================================================================


@router.get("/.well-known/oauth-protected-resource", include_in_schema=False)
@router.get(
    "/.well-known/oauth-protected-resource/{path:path}", include_in_schema=False
)
async def oauth_protected_resource(path: str = ""):
    """OAuth 2.0 Protected Resource Metadata (RFC 8707)."""
    return {
        "resource": _AUTH_SETTINGS.BASE_URL,
        "authorization_servers": _AUTH_SETTINGS.authorization_servers,
        "bearer_methods_supported": ["header"],
        "scopes_supported": _AUTH_SETTINGS.scopes_supported,
    }


@router.get("/.well-known/oauth-authorization-server", include_in_schema=False)
async def oauth_authorization_server():
    """OAuth 2.0 Authorization Server Metadata (RFC 8414)."""
    return {
        "issuer": _AUTH_SETTINGS.issuer,
        "authorization_endpoint": _AUTH_SETTINGS.authorization_endpoint,  # f"{descope_base}/oauth2/v1/authorize",
        "token_endpoint": _AUTH_SETTINGS.token_endpoint,  # f"{descope_base}/oauth2/v1/token",
        "jwks_uri": _AUTH_SETTINGS.jwks_url,  # f"{descope_base}/.well-known/jwks.json",
        "response_types_supported": _AUTH_SETTINGS.response_types_supported,
        "grant_types_supported": _AUTH_SETTINGS.grant_types_supported,
        "token_endpoint_auth_methods_supported": _AUTH_SETTINGS.token_endpoint_auth_methods_supported,
        "scopes_supported": _AUTH_SETTINGS.scopes_supported,
    }


@router.get("/.well-known/openid-configuration", include_in_schema=False)
async def openid_configuration():
    """OpenID Connect Discovery endpoint."""
    return {
        "issuer": _AUTH_SETTINGS.issuer,
        "authorization_endpoint": _AUTH_SETTINGS.authorization_endpoint,
        "token_endpoint": _AUTH_SETTINGS.token_endpoint,
        "userinfo_endpoint": _AUTH_SETTINGS.userinfo_endpoint,
        "jwks_uri": _AUTH_SETTINGS.jwks_url,
        "response_types_supported": _AUTH_SETTINGS.response_types_supported,
        "subject_types_supported": _AUTH_SETTINGS.subject_types_supported,
        "id_token_signing_alg_values_supported": _AUTH_SETTINGS.id_token_signing_alg_values_supported,
        "scopes_supported": _AUTH_SETTINGS.scopes_supported,
        "token_endpoint_auth_methods_supported": _AUTH_SETTINGS.token_endpoint_auth_methods_supported,
        "claims_supported": _AUTH_SETTINGS.claims_supported,
    }
