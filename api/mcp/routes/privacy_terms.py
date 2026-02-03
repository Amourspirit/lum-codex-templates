from pathlib import Path
from fastmcp import FastMCP
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastapi import HTTPException


def register_routes(mcp: FastMCP):
    @mcp.resource(
        "resource://privacy_terms",
        tags=set(["privacy-terms"]),
        title="Privacy Policy",
        description="Retrieve the privacy policy HTML content.",
        mime_type="text/html",
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    async def privacy_terms_route(ctx: Context = CurrentContext()):
        # Internally, you could call your resource logic here
        # return JSONResponse({"message": "Hello from resource"})
        path = Path("api/html/privacy_policy.html")
        if not path.exists():
            raise HTTPException(
                status_code=404, detail="Privacy Policy file not found."
            )
        html_content = path.read_text()  # Read the file content as text
        return html_content
        # return ContentResponse(content=html_content)
