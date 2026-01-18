from typing import Optional
import urllib.request
import httpx
from fastapi import APIRouter, HTTPException, Security, Request
from fastapi.responses import RedirectResponse
from ...lib.descope.auth import TokenVerifier
from ...lib.env import env_info

# Set a custom User-Agent to avoid being blocked by security filters or rate limiters.
opener = urllib.request.build_opener()
# opener.addheaders.append(("User-agent", "Mozilla/5.0 (DescopeFastAPISampleApp)"))
opener.addheaders.append(("User-agent", "Mozilla/5.0 (CodexTemplatesFastAPIApp)"))

urllib.request.install_opener(opener)

auth = TokenVerifier()

router = APIRouter(tags=["Descope Route Protection"])

_DESCOPE_TOKEN_URL = "https://api.descope.com/oauth2/v1/apps/token"

_DESCOPE_AUTHORIZE_URL = "https://api.descope.com/oauth2/v1/apps/authorize"


@router.get("/api/private")
def private(auth_result: str = Security(auth)):
    # This API is now protected by our TokenVerifier object `auth`
    return auth_result


@router.get("/api/private-scoped/read")
def private_scoped(auth_result: str = Security(auth, scopes=["read:messages"])):
    """
    This is a protected route with scope-based access control.

    Access to this endpoint requires:
    - A valid access token (authentication), and
    - The presence of the `read:messages` scope in the token.
    """
    return auth_result


@router.get("/authorize")
async def authorize(
    request: Request,
    response_type: Optional[str] = None,
    redirect_uri: Optional[str] = None,
    scope: Optional[str] = None,
    state: Optional[str] = None,
):
    """
    OAuth 2.0 Authorization Endpoint - Proxies to Descope

    This endpoint forwards OAuth authorization requests to Descope's Inbound Apps.
    """

    try:
        # Validate required parameters
        if not redirect_uri or not response_type:
            print("Missing required parameters")
            raise HTTPException(status_code=400)

        # Validate response_type
        if response_type != "code":
            print(f"Unsupported response_type: {response_type}")
            raise HTTPException(status_code=400)

        # Get client ID from environment or use the provided one

        if not env_info.DESCOPE_INBOUND_APP_CLIENT_ID:
            print("OAuth client credentials not configured")
            raise HTTPException(
                status_code=500,
            )

        # Get the base URL from the request
        base_url = str(request.base_url).rstrip("/")
        callback_url = f"{base_url}/api/oauth/callback"

        # Construct query parameters
        params = {
            "client_id": env_info.DESCOPE_INBOUND_APP_CLIENT_ID,
            "redirect_uri": callback_url,
            "response_type": "code",
            "scope": scope or "openid",
            "state": state or "",  # Just pass through the state parameter
        }

        # Build the full URL with query parameters
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{_DESCOPE_AUTHORIZE_URL}?{query_string}"

        print(f"Redirecting to Descope: {full_url}")

        # Redirect to Descope's authorization endpoint
        return RedirectResponse(url=full_url)

    except HTTPException:
        raise
    except Exception as error:
        print(f"Authorization endpoint error: {error}")
        raise HTTPException(status_code=500)


@router.post("/token")
async def token(request: Request):
    """
    OAuth 2.0 Token Endpoint - Proxies to Descope

    This endpoint forwards token exchange requests to Descope's Inbound Apps.
    """
    print("Token exchange request received")

    try:
        # Parse the request body based on content type
        content_type = request.headers.get("content-type", "")
        print(f"Request content-type: {content_type}")

        if "application/json" in content_type:
            body = await request.json()
        elif "application/x-www-form-urlencoded" in content_type:
            form_data = await request.form()
            body = dict(form_data)
        else:
            # Try to parse as JSON first, then as form data
            try:
                body = await request.json()
            except Exception:
                form_data = await request.form()
                body = dict(form_data)

        grant_type = body.get("grant_type")
        code = body.get("code")
        client_id = env_info.DESCOPE_INBOUND_APP_CLIENT_ID
        client_secret = env_info.DESCOPE_INBOUND_APP_CLIENT_SECRET

        # Validate required parameters
        if not grant_type or not code or len(client_id) == 0 or len(client_secret) == 0:
            raise HTTPException(status_code=400)

        # Only support authorization_code grant type
        if grant_type != "authorization_code":
            raise HTTPException(status_code=400)

        # Get the base URL from the request
        base_url = str(request.base_url).rstrip("/")
        callback_url = f"{base_url}/api/oauth/callback"

        # Forward the request to Descope's token endpoint
        token_request_body = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": callback_url,
        }

        async with httpx.AsyncClient() as client:
            print("Sending request to Descope token endpoint")
            response = await client.post(
                _DESCOPE_TOKEN_URL,
                data=token_request_body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            descope_data = response.json()

            # If Descope returned an error, log it
            if response.status_code >= 400:
                print(f"Descope token exchange failed: {descope_data}")

            # Return the response from Descope
            return descope_data

    except HTTPException:
        raise
    except Exception as error:
        print(f"Token endpoint error: {error}")
        raise HTTPException(status_code=500)


@router.get("/api/oauth/callback")
async def oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    """
    OAuth 2.0 Callback Endpoint

    Handles the callback from Descope and redirects back to Custom GPT.
    """

    try:
        # Handle errors from Descope
        if error:
            raise HTTPException(
                status_code=400,
                detail={"error": error, "error_description": error_description},
            )

        if not code:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_request",
                    "error_description": "No authorization code received",
                },
            )

        # Custom GPT callback URL - obtained after creating your GPT

        # Build redirect URL back to Custom GPT
        redirect_url = f"{env_info.API_CUSTOM_GPT_CALLBACK_URL}?code={code}"
        if state:
            redirect_url += f"&state={state}"

        return RedirectResponse(url=redirect_url)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "server_error",
                "error_description": "Internal server error",
            },
        )
