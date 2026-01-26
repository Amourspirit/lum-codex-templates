from pathlib import Path
from fastapi import APIRouter, HTTPException
from ..models.html_response import HtmlResponse


router = APIRouter(tags=["Privacy Terms"])


@router.get(
    "/privacy",
    response_model=HtmlResponse,
    operation_id="read_privacy_policy",
    description="Retrieve the privacy policy HTML content.",
    summary="Get Privacy Policy",
)
async def read_privacy_policy() -> HtmlResponse:
    """
    Asynchronously retrieves and serves the privacy policy HTML file.
    Checks for the existence of the privacy policy file at the predefined path.
    If the file exists, it returns a FileResponse; otherwise, it raises a 404 error.
    Returns:
        FileResponse: The privacy policy HTML file.
    Raises:
        HTTPException: 404 status code if the privacy policy file is not found.
    """

    path = Path("api/html/privacy_policy.html")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Privacy Policy file not found.")
    return HtmlResponse(content=path.read_text())
