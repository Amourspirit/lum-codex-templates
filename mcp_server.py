import os
from fastmcp import FastMCP

# from fastmcp.server.auth.providers.descope import DescopeProvider
from api.lib.descope.descope_provider import DescopeProvider
from starlette.responses import FileResponse, JSONResponse
from api.lib.descope.auth_config import get_settings
from api.mcp.routes import templates
from api.mcp.routes import executor_modes

_SETTINGS = get_settings()


# Create the Descope auth provider
auth = DescopeProvider(
    config_url=_SETTINGS.FASTMCP_SERVER_AUTH_DESCOPEPROVIDER_CONFIG_URL,
    project_id=_SETTINGS.DESCOPE_PROJECT_ID,
    base_url=_SETTINGS.FASTMCP_SERVER_AUTH_DESCOPEPROVIDER_BASE_URL,
    descope_base_url=_SETTINGS.DESCOPE_API_BASE_URL,
)

# Create FastMCP server with the configured Descope auth provider


mcp = FastMCP(name="Codex Templates MCP Server", auth=auth)


# Create the app with the MCP path
app = mcp.http_app(path="/mcp", transport="http")

templates.register_routes(mcp)
executor_modes.register_routes(mcp)


@app.route("/", methods=["GET"])
async def serve_index():
    return JSONResponse(
        content={"message": "Welcome! Please login to access the API documentation."}
    )


if __name__ == "__main__":
    if os.getenv("LOCAL_DEV_MODE", "false").lower() == "true":
        import uvicorn

        port = int(
            os.getenv("PORT", 8000)
        )  # Use env PORT for deployment (e.g., Render.com)
        uvicorn.run(app, host="localhost", port=port)
