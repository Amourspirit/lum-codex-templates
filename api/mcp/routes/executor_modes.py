import json
from pathlib import Path
from fastmcp import FastMCP
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


_PKG_CONFIG = PkgConfig()

_TEMPLATE_DIR = _PKG_CONFIG.api_info.info_templates.dir_name


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
    if not session.validate_roles(["mcp.template.user"], match_any=True):
        logger.error("User does not have the required role to access templates.")
        raise Exception("User does not have the required role to access templates.")
    if not session.validate_scopes(["mcp.template:read"], match_any=True):
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


def register_routes(mcp: FastMCP):
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
        path = Path(f"api/{_TEMPLATE_DIR}/executor_modes/{ver}/cbib.json")
        if not path.exists():
            raise HTTPException(status_code=404, detail="CBIB file not found.")
        json_content = json.loads(path.read_text())
        return CbibResponse(**json_content)

    @mcp.tool(
        title="Get Template CBIB",
        description="Retrieve the CBIB file for a specific executor mode version that is use in Codex templates, Usually the `resource://default_cbib` resource can be used instead unless a specific version is needed.",
        tags=set(["codex-template", "executor-modes"]),
    )
    async def get_template_cbib(
        input: ArgTemplateVersion, ctx: Context = CurrentContext()
    ) -> CbibResponse:
        return await _get_template_cbib_internal(input)

    @mcp.resource(
        "resource://default_cbib",
        title="Default CBIB",
        mime_type="application/json",
        tags=set(["codex-template", "executor-modes"]),
        description="Use this resource when the CBIB for applying executor mode to codex templates.",
    )
    async def default_template_cbib(
        ctx: Context = CurrentContext(),
    ) -> CbibResponse:
        default_version = _PKG_CONFIG.template_cbib_api.version
        v_result = _validate_version_str(f"v{default_version}")
        if not Result.is_success(v_result):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(v_result.error)
            )
        ver = v_result.data

        logger.debug("resource://default_cbib: Default CBIB version: {v}", v=ver)
        # get the default CBIB  from get_template_cbib
        version_input = ArgTemplateVersion(version=ver)
        response = await _get_template_cbib_internal(version_input)
        return response
