import json
from pathlib import Path
from fastmcp import FastMCP
from fastmcp.server.context import Context
from fastapi import HTTPException, status
from loguru import logger
from api.lib.descope.auth import AUTH
from api.lib.util.result import Result
from api.models.descope.descope_session import DescopeSession
from api.models.executor_modes.v1_0.cbib_response import CbibResponse
from src.config.pkg_config import PkgConfig

_TEMPLATE_DIR = PkgConfig().api_info.info_templates.dir_name


async def _validate_executor_access(ctx: Context) -> DescopeSession:
    if ctx.request_context is None:
        raise Exception("Request context is missing in the provided context.")
    if ctx.request_context.request is None:
        raise Exception("Request is missing in the request context.")
    bearer = ctx.request_context.request.headers.get("Authorization")
    token = bearer.split(" ")[1] if bearer else None
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
    @mcp.tool(
        title="Get Template CBIB",
        description="""Retrieve the CBIB file for a specific executor mode version.

- **version**: The version of the executor mode in the format of `vX.Y` or `X.Y`.
""",
        tags=set(["codex-template", "executor-modes"]),
    )
    async def get_template_cbib(version: str, ctx: Context) -> CbibResponse:
        logger.debug("get_template_cbib called")
        try:
            _ = await _validate_executor_access(ctx=ctx)
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")

        v_result = _validate_version_str(version)
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
