import urllib.parse
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
import urllib
from ...lib.descope.client import DESCOPE_CLIENT
from ...lib.env import env_info
from descope.exceptions import AuthException


# Initialize Descope client


# Create FastAPI app without default docs
router = APIRouter(tags=["Descope Login"])


# Session validation dependency
async def get_current_user(request: Request):
    """Validate the session token from cookies or Authorization header."""
    session_token = request.cookies.get("session_token")

    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header[7:]

    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        jwt_response = DESCOPE_CLIENT.validate_session(session_token)
        return jwt_response
    except AuthException as e:
        raise HTTPException(status_code=401, detail=f"Invalid session: {str(e)}")


# Login route - initiates Descope flow
@router.get("/login")
async def login(request: Request):
    """Redirect to Descope authentication flow."""
    # Get the base URL for the redirect
    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/auth/callback"
    encoded_redirect = urllib.parse.quote(redirect_uri, safe="")

    # Generate the Descope flow URL
    flow_url = (
        f"https://auth.descope.io/{env_info.DESCOPE_PROJECT_ID}"
        f"?{env_info.DESCOPE_FLOW_ID}"
        f"&redirectUrl={encoded_redirect}"
    )

    # flow_url = f"https://auth.descope.io/{env_info.DESCOPE_PROJECT_ID}?flow={env_info.DESCOPE_FLOW_ID}&redirect_uri={redirect_uri}"

    return RedirectResponse(url=flow_url)


# Callback route - handles the auth response
@router.get("/auth/callback")
async def auth_callback(request: Request, response: Response):
    """Handle the callback from Descope after authentication."""
    code = request.query_params.get("code")

    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")

    try:
        # Exchange the code for session tokens
        jwt_response = DESCOPE_CLIENT.exchange_access_key(code)

        # Set session token in HTTP-only cookie
        response = RedirectResponse(url="/docs", status_code=302)
        response.set_cookie(
            key="session_token",
            value=jwt_response["sessionJwt"],
            httponly=True,
            secure=True,  # Set to False for local development without HTTPS
            samesite="lax",
            max_age=3600,  # 1 hour
        )

        # Optionally set refresh token
        if jwt_response.get("refreshJwt"):
            response.set_cookie(
                key="refresh_token",
                value=jwt_response["refreshJwt"],
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=86400 * 30,  # 30 days
            )

        return response

    except AuthException as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


# Logout route
@router.get("/logout")
async def logout(request: Request):
    """Log out the user and clear session cookies."""
    session_token = request.cookies.get("session_token")

    if session_token:
        try:
            DESCOPE_CLIENT.logout(session_token)
        except AuthException:
            pass  # Token may already be invalid

    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session_token")
    response.delete_cookie("refresh_token")
    return response
