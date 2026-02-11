import httpx
import json
from loguru import logger
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import markdown_it

# from starlette.responses import Response
from api.lib.descope.auth_config import get_settings

_AUTH_SETTINGS = get_settings()

router = APIRouter(tags=["Authorization", "Authentication"])

# OAuth 2.0 Discovery Endpoints (Required for MCP Inspector v0.19.0)
# ============================================================================


async def _get_mcp_proxy_content(request: Request):
    """
    Standard JSON wrapper for MCP tool calls to help Bruno.

    This endpoint captures JSON-RPC calls intended for the MCP messages endpoint,
    forwards them internally, and returns the response back to the caller as JSON.

    This is just a way to show Response Data as JSON in Bruno instead of SSE format.
    """
    # 1. Capture the incoming JSON-RPC call and headers
    payload = await request.json()
    headers = {
        "Content-Type": "application/json",
        "Accept": request.headers.get("Accept", ""),
        "Mcp-Session-Id": request.headers.get("Mcp-Session-Id", ""),
        "Authorization": request.headers.get("Authorization", ""),
    }

    # 2. Call the internal MCP messages endpoint
    # Note: We use the full internal URL for your mounted MCP app
    mcp_url = f"{_AUTH_SETTINGS.BASE_URL}/templates/mcp"

    async with httpx.AsyncClient() as client:
        try:
            # We append the sessionId to the URL if it exists
            session_id = headers.get("Mcp-Session-Id")
            url = f"{mcp_url}?sessionId={session_id}" if session_id else mcp_url

            resp = await client.post(url, json=payload, headers=headers, timeout=30.0)
            raw_text = resp.text

            # 3. Unwrap the SSE 'data:' format
            if "data: " in raw_text:
                # Split by 'data: ' and take the first valid JSON block
                lines = raw_text.split("\n")
                for line in lines:
                    if line.startswith("data: "):
                        json_str = line.replace("data: ", "").strip()
                        # response.headers["mcp-session-id"] = session_id or ""
                        return json.loads(json_str)

            # Fallback if the response wasn't SSE
            return resp.json()

        except Exception as e:
            logger.error(f"Proxy error: {str(e)}")
            raise e


@router.post("/bruno/tools/call")
async def bruno_mcp_proxy(request: Request):
    """
    Standard JSON wrapper for MCP tool calls to help Bruno.

    This endpoint captures JSON-RPC calls intended for the MCP messages endpoint,
    forwards them internally, and returns the response back to the caller as JSON.

    This is just a way to show Response Data as JSON in Bruno instead of SSE format.
    """
    # 1. Capture the incoming JSON-RPC call and headers
    session_id = request.headers.get("Mcp-Session-Id", "")
    try:
        json_content = await _get_mcp_proxy_content(request)
        return JSONResponse(
            content=json_content,
            headers={"mcp-session-id": session_id},
        )
    except Exception as e:
        logger.error(f"Proxy error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Proxy failed to reach MCP", "details": str(e)},
            headers={"mcp-session-id": session_id},
        )


@router.post("/bruno/tools/call/markdown")
async def bruno_mcp_proxy_markdown(request: Request):
    """
    Async endpoint that proxies MCP (Model Context Protocol) requests and returns markdown content.
    This function retrieves structured content from an MCP proxy request, extracts the markdown
    content from the nested response structure, and returns it with the appropriate media type.
    Args:
        request (Request): The incoming HTTP request object containing headers and body data.
            Expected header: 'Mcp-Session-Id' for session tracking.
    Returns:
        JSONResponse: A JSON response containing the markdown content with:
            - content: The extracted markdown string from the MCP response
            - media_type: "text/markdown"
            - headers: Includes the original 'mcp-session-id' for session tracking
            - status_code: 200 on success, 500 on error
    Raises:
        Exception: Any exception from the MCP proxy call is caught and returned as a 500 error
            response with error details included in the response body.
    Side Effects:
        - Logs errors to the logger if the MCP proxy request fails
    """
    
    session_id = request.headers.get("Mcp-Session-Id", "")
    try:
        json_content = await _get_mcp_proxy_content(request)
        markdown_content = (
            json_content.get("result", {})
            .get("structuredContent", {})
            .get("content", "")
        )
        return JSONResponse(
            content=markdown_content,
            media_type="text/markdown",
            headers={"mcp-session-id": session_id},
        )

    except Exception as e:
        logger.error(f"Proxy error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Proxy failed to reach MCP", "details": str(e)},
            headers={"mcp-session-id": session_id},
        )
