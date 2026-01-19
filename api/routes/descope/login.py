import urllib.parse
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
import urllib
from ...lib.descope.client import DESCOPE_CLIENT
from ...lib.env import env_info
from descope.exceptions import AuthException


# Initialize Descope client


# Create FastAPI app without default docs
router = APIRouter(tags=["Descope Login"])


# Session validation dependency


# Login route - initiates Descope flow
@router.get("/login")
async def login(request: Request):
    """Redirect to Descope authentication flow."""
    try:
        # Get the base URL for the redirect
        base_url = str(request.base_url).rstrip("/")
        redirect_uri = f"{base_url}/auth/callback"
        encoded_redirect = urllib.parse.quote(redirect_uri, safe="")
        redirect_url = str(request.url_for("callback"))

        # Generate the Descope flow URL
        flow_url = (
            f"https://api.descope.com/flow/{env_info.DESCOPE_FLOW_ID}"
            f"&returnUrl={encoded_redirect}"
        )

        return JSONResponse(
            content={"redirect_url": flow_url, "flow_id": env_info.DESCOPE_FLOW_ID}
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Authentication flow start failed: {str(e)}"
        )


@router.get("/callback")
async def callback(request: Request):
    """
    Handle the callback from Descope after authentication
    """
    try:
        # Extract the code or tokens from the query parameters
        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")

        # Exchange the authorization code for tokens
        # Note: The exact method depends on the authentication method used
        # For OAuth flows, you might use auth.oauth_exchange_token(code)
        # For other flows, the method might be different

        # Since this is a flow-based authentication, we need to validate the session
        # The callback may contain session information that needs to be processed
        auth_info = DESCOPE_CLIENT.validate_session(code)

        return JSONResponse(
            content={
                "success": True,
                "session_token": auth_info.get("sessionJwt"),
                "user": auth_info.get("user", {}),
                "message": "Authentication successful",
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Callback processing failed: {str(e)}"
        )


@router.post("/verify-session")
async def verify_session_endpoint(request: Request):
    """
    Verify a session token
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")

        token = auth_header[7:]

        # Verify the session token
        verified_token = DESCOPE_CLIENT.validate_session(token)

        return JSONResponse(
            content={
                "valid": True,
                "user_id": verified_token.get("userId"),
                "tenants": verified_token.get("tenants", {}),
                "message": "Session verified successfully",
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=401, detail=f"Session verification failed: {str(e)}"
        )


@router.post("/logout")
async def logout(request: Request):
    """
    Logout endpoint to invalidate the session
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")

        token = auth_header[7:]

        # Logout the user (invalidate the session)
        DESCOPE_CLIENT.logout(token)

        return JSONResponse(content={"message": "Successfully logged out"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")


# Alternative implementation for flow-based auth using embedded widgets
@router.get("/embedded-login")
async def embedded_login(request: Request):
    """
    Alternative approach for embedded flow-based authentication
    """
    try:
        # For embedded flows, you would typically return a session token
        # that can be used with the Descope Web Components
        # tenant = os.getenv("DESCOPE_TENANT", "")  # Optional tenant

        # Start the flow and return necessary data for the frontend
        flow_data = {
            "project_id": env_info.DESCOPE_PROJECT_ID,
            "flow_id": env_info.DESCOPE_FLOW_ID,
            "base_url": "https://api.descope.com",
            # "tenant": tenant
        }

        return JSONResponse(content=flow_data)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Embedded login setup failed: {str(e)}"
        )


def get_current_user(request: Request):
    """
    Helper dependency to get current authenticated user
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header[7:]
    try:
        return DESCOPE_CLIENT.validate_session(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.get("/protected-route")
async def protected_route(current_user: dict = Depends(get_current_user)):
    """
    Example of a protected route that requires authentication
    """
    return {
        "message": "This is a protected route",
        "user": current_user.get("user", {}),
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "FastAPI with Descope Auth"}
