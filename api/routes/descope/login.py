from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates  # Import this
from ...lib.env import env_info

router = APIRouter(tags=["Login"])
templates = Jinja2Templates(
    directory="api/api_templates"
)  # Create a 'templates' folder


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Serves an HTML page that embeds the Descope Flow.
    This keeps the user on YOUR domain, preventing cookie/state errors.
    """
    base_url = str(request.base_url).rstrip("/")
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "project_id": env_info.DESCOPE_PROJECT_ID,
            "flow_id": env_info.DESCOPE_FLOW_ID,
            "redirect_url": f"{base_url}/callback",  # Success will redirect here
        },
    )


@router.get("/callback")
def callback(session_token: str | None = None, code: str | None = None):
    # This route remains the same as before!
    # The embedded flow will redirect here with 'session_token' or 'code'
    # when the user finishes successfully.

    # ... your existing cookie setting logic ...
    print("Redirecting to /docs")
    response = RedirectResponse(url="/docs")
    if session_token:
        response.set_cookie(
            key="session_token", value=session_token, httponly=True, secure=True
        )

    return response
