import httpx
import secrets
from descope.descope_client import DescopeClient
from fastapi import APIRouter
from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from api.lib.descope.auth_config import get_settings
from api.models.descope.descope_session import DescopeSession
from api.lib.descope.session import get_descope_session, get_user_session

_AUTH_SETTINGS = get_settings()
_DESCOPE_CLIENT = DescopeClient(project_id=_AUTH_SETTINGS.DESCOPE_PROJECT_ID)

router = APIRouter(tags=["Authorization", "Authentication"])

# OAuth 2.0 Discovery Endpoints (Required for MCP Inspector v0.19.0)
# ============================================================================


# region Login/Logout Routes
@router.get("/login")
def login(request: Request):
    """
    Redirects to Descope for auth, BUT skips if already logged in.
    """
    # --- Check if already logged in ---
    if get_user_session(request):
        return RedirectResponse(url="/dashboard")

    # Generate a secure random state
    state = secrets.token_urlsafe(32)

    # We construct the standard OAuth2 authorization URL
    params = {
        "response_type": "code",
        "client_id": _AUTH_SETTINGS.DESCOPE_INBOUND_APP_CLIENT_ID,
        "redirect_uri": _AUTH_SETTINGS.api_callback_url,  # Must match the one registered in Descope and used in /callback
        # "scope": "login_access api.context:read profile email profile",
        "scope": "login_access api.context:read email profile",  # Standard scopes
        "state": state,
    }

    # Build the full URL: https://api.descope.com/oauth2/v1/apps/authorize?response_type=code...
    auth_url = (
        _AUTH_SETTINGS.authorization_endpoint
    )  # https://api.descope.com/oauth2/v1/apps/authorize
    url_request = httpx.Request("GET", auth_url, params=params)
    response = RedirectResponse(url=str(url_request.url))

    # Save the state in a cookie to verify later
    #    We set max_age to 300 (5 mins) because the login process shouldn't take longer.
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        samesite="lax",
        secure=_AUTH_SETTINGS.is_production,  # Only set secure cookies in production (HTTPS)
        max_age=300,
    )

    return response


@router.get("/logout")
def logout(request: Request):
    """
    Logs the user out by:
    1. Revoking the session at Descope (Server-side).
    2. Deleting the cookies (Client-side).
    3. Redirecting to the home page.
    """
    response = RedirectResponse(url="/")

    # 1. Get the refresh token to revoke the session
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        try:
            # Tell Descope this refresh token is now garbage
            _DESCOPE_CLIENT.logout(refresh_token)
        except Exception as e:
            # If it fails (e.g., token already expired), we don't care.
            # We still want to clear the cookies on our side.
            print(f"Descope logout failed (non-critical): {e}")

    # 2. Clear the cookies
    # You must use the same domain/path/secure settings as when you set them
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    response.delete_cookie(key="refresh_token", httponly=True, samesite="lax")

    return response


@router.get("/dashboard")
def dashboard(session_user: DescopeSession = Depends(get_descope_session)):
    return {
        "message": "Welcome to the secret dashboard",
        "user_email": session_user.email,
        "user_id": session_user.user_id,
    }


@router.get("/callback")
async def callback(code: str, state: str | None, request: Request):
    """
    2. Descope redirects the user back here with a 'code'.
    3. We exchange that code for an Access Token.
    """
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")

    saved_state = request.cookies.get("oauth_state")

    # Security Check: Compare URL state vs Cookie state
    if not saved_state or saved_state != state:
        raise HTTPException(
            status_code=400, detail="Invalid state parameter (CSRF detected)"
        )

    async with httpx.AsyncClient() as client:
        # Prepare the payload to exchange code for token
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": _AUTH_SETTINGS.api_callback_url,  # Must match the one used in /login
            "client_id": _AUTH_SETTINGS.DESCOPE_INBOUND_APP_CLIENT_ID,
            "client_secret": _AUTH_SETTINGS.DESCOPE_INBOUND_APP_CLIENT_SECRET,
        }

        # Make the server-to-server POST request to Descope
        response = await client.post(_AUTH_SETTINGS.token_endpoint, data=token_data)

        if response.status_code != 200:
            raise HTTPException(
                status_code=400, detail=f"Failed to get token: {response.text}"
            )

        tokens = response.json()

        # tokens usually contains: access_token, id_token, refresh_token, etc.
        # You can now use 'access_token' to access Descope APIs or verify the user.

        # return {
        #     "status": "Success",
        #     "message": "User successfully logged in via Descope Inbound App",
        #     "tokens": tokens,
        # }
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        max_age = tokens.get("expires_in", 3600)  # Default to 1 hour if not provided

        redirect_response = RedirectResponse(url="/docs")

        secure = (
            _AUTH_SETTINGS.is_production
        )  # Only set secure cookies in production (HTTPS)

        # Set the token in a Secure, HttpOnly cookie
        # httponly=True means JavaScript cannot steal it (XSS protection)
        # samesite="lax" protects against CSRF
        redirect_response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=secure,  # Set to True in production (HTTPS)
            samesite="lax",
            max_age=max_age,  # Set to match token expiry
        )
        # Optionally, you can also set the refresh token in a cookie or handle it differently
        redirect_response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=secure,  # Set to True in production (HTTPS)
            samesite="lax",
            max_age=max_age,
        )

        # IMPORTANT: Delete the temporary state cookie
        redirect_response.delete_cookie("oauth_state")

        return redirect_response


# endregion Login/Logout Routes
