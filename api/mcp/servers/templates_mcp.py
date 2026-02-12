from typing import Any, cast
from loguru import logger
from fastmcp import FastMCP
from api.mcp.routes import templates as mcp_templates
from api.mcp.routes import executor_modes as mcp_executor_modes
from api.mcp.routes import privacy_terms as mcp_privacy_terms
from api.mcp.routes import ping as mcp_ping
from api.lib.descope.auth_config import get_settings

_SETTINGS = get_settings()

mcp = cast(FastMCP, None)


def init_mcp(auth: Any = None) -> FastMCP:
    global mcp
    if mcp is None:
        if auth is None:
            mcp = FastMCP(name="Codex Templates MCP Server")
            logger.debug("Initialized MCP without auth provider")

        else:
            mcp = FastMCP(name="Codex Templates MCP Server", auth=auth)
            logger.debug("Initialized MCP with auth provider")

        mcp_templates.register_routes(mcp)
        mcp_executor_modes.register_routes(mcp)
        mcp_privacy_terms.register_routes(mcp)
        mcp_ping.register_routes(mcp)
        logger.debug("Registered MCP routes")

    return mcp
