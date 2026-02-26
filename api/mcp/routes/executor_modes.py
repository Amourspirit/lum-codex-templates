import json
from fastmcp import FastMCP
from fastmcp.exceptions import ResourceError
from fastmcp.server.context import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.server.dependencies import get_http_headers
from fastapi import HTTPException, status
from loguru import logger
from api.lib.descope.auth import AUTH
from api.lib.util.result import Result
from api.models.descope.descope_session import DescopeSession
from api.models.executor_modes.v1_0.cbib_response import CbibResponse
from src.config.pkg_config import PkgConfig
from api.models.args import ArgTemplateVersion


_SETTINGS = PkgConfig()

# _TEMPLATE_DIR = _SETTINGS.api_info.info_templates.dir_name
_CBIB_PATH = _SETTINGS.config_cache.get_api_cbib_path()


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


def _validate_version_str(version: str) -> Result[str, None] | Result[None, Exception]:
    if not version:
        return Result(None, Exception("Version is required."))
    v = version.strip().lower()
    v = v.lstrip("v")
    if not v:
        return Result(None, Exception("Version cannot be empty."))
    if not v.replace(".", "").isdigit():
        return Result(None, Exception("Invalid version format."))
    if v.isdigit():
        v = f"{v}.0"
    if not v.startswith("v"):
        v = "v" + v
    return Result(v, None)


async def _get_template_cbib_internal(input: ArgTemplateVersion) -> CbibResponse:
    logger.debug("get_template_cbib called")
    try:
        _ = await _header_validate_access()
    except Exception as e:
        raise Exception(f"Authentication failed: {str(e)}")

    v_result = _validate_version_str(input.version)
    if not Result.is_success(v_result):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(v_result.error)
        )
    ver = v_result.data
    path = _CBIB_PATH / ver / "cbib.json"
    if not path.exists():
        raise ResourceError("CBIB file not found.")
    json_content = json.loads(path.read_text())
    return CbibResponse(**json_content)


def register_routes(mcp: FastMCP):
    # region Resources
    @mcp.resource(
        "executor-mode://executor_mode/{version}",
        title="Get Template Executor Mode (CBIB) by Version",
        mime_type="application/json",
        description="Use this executor_mode resource when retrieving the Executor Mode (CBIB) file for a specific executor mode version that is used in Codex templates. Usually the `executor_mode://default_executor_mode` resource can be used instead unless a specific version is needed.",
        tags=set(["codex-template", "executor-modes"]),
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "destructiveHint": False,
        },
    )
    async def template_executor_mode_resource(
        version: str, ctx: Context = CurrentContext()
    ) -> CbibResponse:
        return await _get_template_cbib_internal(ArgTemplateVersion(version=version))

    @mcp.resource(
        "executor-mode://default_executor_mode",
        title="Default Executor Mode (CBIB)",
        mime_type="application/json",
        tags=set(["codex-template", "executor-modes"]),
        description="Use this executor_mode resource when the for applying default executor mode to codex templates.",
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "destructiveHint": False,
        },
    )
    async def default_template_executor_mode_resource(
        ctx: Context = CurrentContext(),
    ) -> CbibResponse:
        default_version = _SETTINGS.template_cbib_api.version
        v_result = _validate_version_str(f"v{default_version}")
        if not Result.is_success(v_result):
            raise ResourceError(str(v_result.error))
        ver = v_result.data

        logger.debug("resource://default_cbib: Default CBIB version: {v}", v=ver)
        # get the default CBIB  from get_template_cbib
        version_input = ArgTemplateVersion(version=ver)
        response = await _get_template_cbib_internal(version_input)
        return response

    # endregion Resources

    # region Tools
    @mcp.tool(
        name="get_canonical_executor_mode",
        title="Get Template Executor Mode (CBIB) by Version",
        description="Use this tool when asked to retrieve the Canonical Executor Mode (CBIB) for a specific executor mode version that is used in Codex templates.",
        tags=set(["codex-template", "executor-modes"]),
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "destructiveHint": False,
        },
    )
    async def template_executor_mode_tool(
        version: str, ctx: Context = CurrentContext()
    ) -> CbibResponse:
        return await _get_template_cbib_internal(ArgTemplateVersion(version=version))

    @mcp.tool(
        name="get_default_canonical_executor_mode",
        title="Get Template Executor Mode (CBIB) latest version",
        description="Use this tool when asked to retrieve the default Canonical Executor Mode (CBIB) that is used in Codex templates.",
        tags=set(["codex-template", "executor-modes"]),
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "destructiveHint": False,
        },
    )
    async def get_default_template_executor_mode_tool(
        ctx: Context = CurrentContext(),
    ) -> CbibResponse:
        default_version = _SETTINGS.template_cbib_api.version
        v_result = _validate_version_str(f"v{default_version}")
        if not Result.is_success(v_result):
            raise ResourceError(str(v_result.error))
        ver = v_result.data

        logger.debug("resource://default_cbib: Default CBIB version: {v}", v=ver)
        # get the default CBIB  from get_template_cbib
        version_input = ArgTemplateVersion(version=ver)
        response = await _get_template_cbib_internal(version_input)
        return response

    # endregion Tools
