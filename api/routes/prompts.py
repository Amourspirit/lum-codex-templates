import json
from loguru import logger
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from ..models.descope.descope_session import DescopeSession
from ..responses.markdown_response import MarkdownResponse
from ..lib.descope.session import get_descope_session
from ..lib.env import env_info
from ..lib.routes import fn_versions
from ..lib.routes import mcp_path

_TEMPLATE_SCOPE = env_info.get_api_scopes("templates")

router = APIRouter(prefix="/api/v1/prompts", tags=["Prompts"])
_API_RELATIVE_URL = "/api/v1"


# region Helper Functions
def _get_latest_template_version(template_type: str) -> str:
    """
    Helper function to get the latest version of a given template type.
    Returns the highest version string or None if not found.
    """
    ver = fn_versions.get_latest_version_for_template(template_type, v_prefix=True)
    typ = template_type.lower()
    if not ver:
        raise ValueError(f"Template type '{typ}' not found.")
    return ver


# endregion Helper Functions


# region Template Prompts
@router.get(
    "/upgrade_template/{template_type}/{artifact_name}",
    response_class=MarkdownResponse,
    operation_id="prompt_template_upgrade",
    description="Retrieve a structured prompt for upgrading an artifact to the latest version of a specified template type. The prompt includes instructions, template content, and registry information to guide the upgrade process.",
    summary="Retrieve a structured prompt for upgrading an artifact to the latest template version",
)
async def get_upgrade_template_prompt(
    template_type: str,
    artifact_name: str,
    request: Request,
    response: Response,
    session: DescopeSession = Depends(get_descope_session),
):

    if session:
        if not session.scopes.intersection(_TEMPLATE_SCOPE.read_scopes):
            logger.error("Insufficient scope to access template registry.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to access template registry.",
            )
    else:
        logger.error("Authentication required to access template registry.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access template registry.",
        )

    tt = template_type.strip().lower()
    if not tt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template type is required.",
        )

    try:
        latest_version = _get_latest_template_version(template_type)
        logger.debug(
            "No version specified. Using latest version: {version}",
            version=latest_version,
        )
    except ValueError as e:
        logger.error(str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if artifact_name:
        response.headers["X-Artifact-Name"] = artifact_name

    tool_rpcs = mcp_path.get_mcp_tool_call_rpc(
        template_type=tt, version=latest_version, artifact_name=artifact_name
    )

    template_tool = tool_rpcs["template_tool"]
    instructions_tool = tool_rpcs["instructions_tool"]
    registry_tool = tool_rpcs["registry_tool"]
    # manifest_tool = tool_rpcs["manifest_tool"]
    executor_mode_tool = mcp_path.get_mcp_executor_mode_rpc()

    template_content_placeholder = "< template_content_with_frontmatter >"
    verify_tool = mcp_path.get_mcp_verify_template_rpc(
        artifact_name=artifact_name, template_content=template_content_placeholder
    )
    finalize_tool = mcp_path.get_mcp_finalize_template_rpc(
        artifact_name=artifact_name, template_content=template_content_placeholder
    )

    template_tool_json = json.dumps(template_tool, indent=2)
    instructions_tool_json = json.dumps(instructions_tool, indent=2)
    registry_tool_json = json.dumps(registry_tool, indent=2)
    # manifest_tool_json = json.dumps(manifest_tool, indent=2)
    verify_tool_json = json.dumps(verify_tool, indent=2)
    finalize_tool_json = json.dumps(finalize_tool, indent=2)
    executor_mode_tool_json = json.dumps(executor_mode_tool, indent=2)

    system_content = (
        "## System Instructions  \n\n"
        "**You are an assistant that can:**\n"
        "\n"
        f"- Call tools (e.g. `{template_tool['params']['name']}`) to perform active queries.\n"
        "\n"
        "### Available tools:\n\n"
        f"#### **{template_tool['params']['name']}**\n"
        "\n"
        "Use this when you need to get the full template content for a specific type and version.\n"
        "\n"
        f"##### **jsonrpc** format for calling tool **{template_tool['params']['name']}**\n"
        "\n"
        "```json\n"
        f"{template_tool_json}\n"
        "```\n"
        "\n"
        f"#### **{instructions_tool['params']['name']}**\n"
        "\n"
        "Use this when you need to get the instructions on how to apply templates.\n"
        "\n"
        f"##### **jsonrpc** format for calling tool **{instructions_tool['params']['name']}**\n"
        "\n"
        "```json\n"
        f"{instructions_tool_json}\n"
        "```\n"
        "\n"
        f"#### **{registry_tool['params']['name']}**\n"
        "\n"
        "Use this when you need to get the registry for the template.\n"
        "This registry determines how the metadata in the template is structured and the rules to apply.\n"
        "\n"
        f"##### **jsonrpc** format for calling tool **{registry_tool['params']['name']}**\n"
        "\n"
        "```json\n"
        f"{registry_tool_json}\n"
        "```\n"
        "\n"
        # f"#### **{manifest_tool['params']['name']}**\n"
        # "\n"
        # "Use this tool when asked to retrieve the Canonical Executor Mode (CBIB) that is used in Codex templates.\n"
        # "\n"
        # f"##### **jsonrpc** format for calling tool **{manifest_tool['params']['name']}**\n"
        # "\n"
        # "```json\n"
        # f"{manifest_tool_json}\n"
        # "```\n"
        # "\n"
        f"#### **{executor_mode_tool['params']['name']}**\n"
        "\n"
        "Use this tool when retrieving the Executor Mode (CBIB) that is used in Codex templates.\n"
        "\n"
        f"##### **jsonrpc** format for calling tool **{executor_mode_tool['params']['name']}**\n"
        "\n"
        "```json\n"
        f"{executor_mode_tool_json}\n"
        "```\n"
        "\n"
        f"#### **{verify_tool['params']['name']}**\n"
        "\n"
        "Use this to verify the metadata fields of a template artifact against the registered schema.\n"
        f"Replace `{template_content_placeholder}` of **jsonrpc** with the actual **json encoded** template markdown content including frontmatter.\n"
        "\n"
        f"##### **jsonrpc** format for calling tool **{verify_tool['params']['name']}**\n"
        "\n"
        "```json\n"
        f"{verify_tool_json}\n"
        "```\n"
        "\n"
        f"#### **{finalize_tool['params']['name']}**\n"
        "\n"
        "Use this to finalize an artifact submission by adding any necessary metadata or performing final validation steps.\n"
        f"Replace `{template_content_placeholder}` of **jsonrpc** with the actual **json encoded** template markdown content including frontmatter.\n"
        "\n"
        f"##### **jsonrpc** format for calling tool **{finalize_tool['params']['name']}**\n"
        "\n"
        "```json\n"
        f"{finalize_tool_json}\n"
        "```\n"
        "\n"
    )

    user_content = (
        "## User Instructions\n\n"
        f"Upgrade the artifact named '{artifact_name}' to the latest template of type `{tt}` of version `{latest_version}`.  \n"
        f"  1. Call tool `{template_tool['params']['name']}` to get the full template content.\n"
        "    - This is the target template apply upgrade.\n"
        f"  2. Call tool `{executor_mode_tool['params']['name']}` to understand the executor mode to apply the template.\n"
        f"  3. Call tool `{registry_tool['params']['name']}` to get the template registry.\n"
        "    - Use this registry to understand the structure and rules for the template metadata.\n"
        f"  4. Call tool `{instructions_tool['params']['name']}` to get the instructions for applying the template.\n"
        "    - Use these instructions to guide the upgrade process.\n"
        "\n"
        "Proceed to upgrade the artifact by applying the template according to the instructions and registry rules.\n"
        "Now that the the upgrade is complete, it is time to verify and finalize the upgraded artifact.\n"
        "\n"
        f"4. Pass the upgraded template content, including the full markdown content with frontmatter, to `{verify_tool['params']['name']}` tool to verify the metadata fields.\n"
        f"5. Next, pass the verified template content to `{finalize_tool['params']['name']}` tool to finalize the artifact submission.\n"
        "6. Provide the finalized artifact as the output."
    )

    return f"{system_content}\n\n{user_content}"


# endregion Template Prompts
