from fastmcp import FastMCP
from fastmcp.server.context import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.server.dependencies import get_http_headers
from fastapi import HTTPException, status
from loguru import logger
from api.lib.descope.auth import AUTH
from api.models.descope.descope_session import DescopeSession
from api.models.session.ping_response import PingResponse


async def _header_validate_access() -> DescopeSession:
    headers = get_http_headers()

    # Get authorization header
    auth_header = headers.get("authorization", "")
    if not auth_header:
        raise Exception("Authorization header is missing.")
    is_bearer = auth_header.startswith("Bearer ")
    if not is_bearer:
        raise Exception("Authorization header must be a Bearer token.")

    token = auth_header.split(" ")[1]
    if not token:
        raise Exception("Access token is required.")
    session = await AUTH.verify_token(token)
    if not session.validate_roles(
        ["mcp.template.user", "mcp:template:user"], match_any=True
    ):
        logger.error("User does not have the required role to access templates.")
        raise Exception("User does not have the required role to access templates.")
    if not session.validate_scopes(
        ["mcp.template:read", "mcp:template:read"], match_any=True
    ):
        logger.error("User does not have the required scope to access templates.")
        raise Exception("User does not have the required scope to access templates.")
    return session


def register_routes(mcp: FastMCP):
    # region Tools
    @mcp.tool(
        name="mcp_ping",
        title="Mcp Ping",
        description="Use this tool when asked to ping the MCP API. Expect 'pong' as the response message. A simple tool to test connectivity and authentication with the MCP API.",
        tags=set(["utility"]),
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    async def mcp_ping(ctx: Context = CurrentContext()) -> PingResponse:
        try:
            _ = await _header_validate_access()
            return PingResponse(message="pong")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    # endregion Tools
