import os
from fastapi.middleware.cors import CORSMiddleware

# from fastmcp.server.auth.providers.descope import DescopeProvider
from api.lib.descope.descope_provider import DescopeProvider
from api.lib.descope.auth_config import get_settings

# from api.mcp.routes import templates as mcp_templates
# from api.mcp.routes import executor_modes as mcp_executor_modes
# from api.mcp.routes import privacy_terms as mcp_privacy_terms
from api.mcp.servers import templates_mcp

_SETTINGS = get_settings()


# Create the Descope auth provider
auth = DescopeProvider(
    config_url=_SETTINGS.FASTMCP_SERVER_AUTH_DESCOPEPROVIDER_CONFIG_URL,
    project_id=_SETTINGS.DESCOPE_PROJECT_ID,
    base_url=_SETTINGS.FASTMCP_SERVER_AUTH_DESCOPEPROVIDER_BASE_URL,
    descope_base_url=_SETTINGS.DESCOPE_API_BASE_URL,
)

# Create the app with the MCP path
mcp_templates = templates_mcp.init_mcp(auth=auth)
app = mcp_templates.http_app(path="/templates/mcp", transport="http")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allows all origins
#     allow_credentials=True,
#     allow_methods=["*"],  # Allows all methods
#     allow_headers=["*"],  # Allows all headers
# )


# @app.route("/", methods=["GET"])
# async def serve_index():
#     return JSONResponse(
#         content={"message": "Welcome! Please login to access the API documentation."}
#     )


if __name__ == "__main__":
    if os.getenv("LOCAL_DEV_MODE", "false").lower() == "true":
        import uvicorn

        port = int(
            os.getenv("PORT", 8000)
        )  # Use env PORT for deployment (e.g., Render.com)
        uvicorn.run(app, host="localhost", port=port)
        # mcp.run(transport="stdio")
