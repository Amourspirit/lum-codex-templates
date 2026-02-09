from pathlib import Path
from fastmcp import FastMCP
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastapi import HTTPException
from api.models.html_response import HtmlResponse


def register_routes(mcp: FastMCP):
    @mcp.resource(
        "resource://privacy_terms",
        tags=set(["privacy-terms"]),
        title="Privacy Policy",
        description="Retrieve the privacy policy HTML content.",
        mime_type="text/html",
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    async def privacy_terms_resource(ctx: Context = CurrentContext()):
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

    @mcp.tool(
        name="privacy_terms",
        tags=set(["privacy-terms"]),
        title="Privacy Policy",
        description="Use this tool when asked to retrieve the privacy policy content.",
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    async def privacy_terms_tool(ctx: Context = CurrentContext()) -> HtmlResponse:
        # Internally, you could call your resource logic here
        # return JSONResponse({"message": "Hello from resource"})
        path = Path("api/html/privacy_policy.html")
        if not path.exists():
            raise HTTPException(
                status_code=404, detail="Privacy Policy file not found."
            )
        html_content = path.read_text()  # Read the file content as text
        return HtmlResponse(content=html_content)
        # return ContentResponse(content=html_content)
