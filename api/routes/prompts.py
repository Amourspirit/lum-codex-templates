import json
from loguru import logger
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Query
from fastapi import Path as ApiPath
from ..models.descope.descope_session import DescopeSession
from ..responses.markdown_response import MarkdownResponse
from ..lib.descope.session import get_descope_session
from ..lib.env import env_info
from ..lib.routes import fn_versions
from ..lib.routes import mcp_path
from ..lib.util.url_helper import encode_url_component

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
    request: Request,
    response: Response,
    template_type: str = ApiPath(
        ...,
        title="Template Type",
        description="The type of the template to upgrade to (e.g. `glyph`, `sigil`, `seal`).",
    ),
    artifact_name: str = ApiPath(
        ...,
        title="Artifact Name",
        description="The name of the artifact to upgrade.",
    ),
    attached_img_name: str | None = Query(
        default=None,
        description="Optional name such as `Glyph` or `Sigil` of an attached image to be included in the prompt.",
    ),
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
        # decode URL-encoded artifact name
        response.headers["X-Artifact-Name"] = encode_url_component(artifact_name)

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
    verify_tool_json = verify_tool_json.replace(
        f'template_content": "{template_content_placeholder}"',
        f'template_content": "{template_content_placeholder}" // Must include YAML + body',
    )

    finalize_tool_json = json.dumps(finalize_tool, indent=2)
    finalize_tool_json = finalize_tool_json.replace(
        f'template_content": "{template_content_placeholder}"',
        f'template_content": "{template_content_placeholder}" // Must include YAML + body',
    )

    executor_mode_tool_json = json.dumps(executor_mode_tool, indent=2)

    ver = latest_version if latest_version.startswith("v") else f"v{latest_version}"

    system_content = (
        "## ⬒ System Instructions  \n\n"
        "**You are an assistant that can:**\n"
        "\n"
        f"- Call tools (e.g. `{template_tool['params']['name']}`) to perform active queries.\n"
        "\n"
        "---\n"
        "\n"
        "### 🧷 Artifact Under Upgrade\n\n"
        f"- `artifact_name`: **{artifact_name}**\n"
        f"- `template_type`: **{template_type}**\n"
        f"- `template_version`: `{ver}`\n"
        "\n"
        "---\n"
        "\n"
        "## ⬒ Tool Reference\n\n"
        f"### **{template_tool['params']['name']}**\n"
        "\n"
        "Use this when you need to get the full template content for a specific type and version.\n"
        "\n"
        "```json\n"
        f"{template_tool_json}\n"
        "```\n"
        "\n"
        f"### **{instructions_tool['params']['name']}**\n"
        "\n"
        "Use this when you need to get the instructions on how to apply templates.\n"
        "\n"
        "```json\n"
        f"{instructions_tool_json}\n"
        "```\n"
        "\n"
        f"### **{registry_tool['params']['name']}**\n"
        "\n"
        "Use this when you need to get the registry for the template.\n"
        "This registry determines how the metadata in the template is structured and the rules to apply.\n"
        "\n"
        "```json\n"
        f"{registry_tool_json}\n"
        "```\n"
        "\n"
        f"### **{executor_mode_tool['params']['name']}**\n"
        "\n"
        "Use this tool when retrieving the Executor Mode (CBIB) that is used in Codex templates.\n"
        "\n"
        "```json\n"
        f"{executor_mode_tool_json}\n"
        "```\n"
        "\n"
        f"### **{verify_tool['params']['name']}**\n"
        "\n"
        "Use this to verify the metadata fields of a template artifact against the registered schema.\n"
        f"Replace `{template_content_placeholder}` of **jsonrpc** with the actual **json encoded** template markdown content including frontmatter.\n"
        "\n"
        "```json\n"
        f"{verify_tool_json}\n"
        "```\n"
        "\n"
        f"### **{finalize_tool['params']['name']}**\n"
        "\n"
        "Use this to finalize an artifact submission by adding any necessary metadata or performing final validation steps.\n"
        f"Replace `{template_content_placeholder}` of **jsonrpc** with the actual **json encoded** template markdown content including frontmatter.\n"
        "\n"
        "```json\n"
        f"{finalize_tool_json}\n"
        "```\n"
    )

    user_content = (
        "\n"
        "---\n"
        "\n"
        "## ⬒ Upgrade Sequence Instructions\n\n"
        f"The purpose of this workflow is to upgrade the artifact **{artifact_name}** to template version `{latest_version}`, using canonical execution rules.\n"
        "\n"
        "Follow this 6-step sequence exactly:\n"
        "\n"
        f"1. **Call** `{template_tool['params']['name']}` to retrieve the canonical target template.\n"
        f"2. **Call** `{executor_mode_tool['params']['name']}` to confirm execution policy.\n"
        f"3. **Call** `{registry_tool['params']['name']}` to retrieve the metadata validation schema.\n"
        f"4. **Call** `{instructions_tool['params']['name']}` to retrieve rendering directives and strict mode rules.\n"
        f"5. **Apply** the upgrade: Render the existing artifact into the new template version, replacing any conditionals or outdated fields.\n"
        f"6. **Verify** using `{verify_tool['params']['name']}`, then **finalize** with `{finalize_tool['params']['name']}`.\n"
        "\n"
        "> ⚠ If any tool fails (e.g. 401, registry mismatch, unresolved placeholders), return the failure output directly. Do not attempt speculative completion.\n"
        "\n"
        "---\n"
        "\n"
    )
    if attached_img_name:
        user_content += (
            "## 🖼️ Attached Image Information\n\n"
            f"- `{attached_img_name}` is included and should be referenced in the upgraded template as needed to aid getting field information.\n"
            "\n"
            "---\n"
            "\n"
        )

    user_content += (
        "## ⬒ Template to Upgrade\n\n"
        "```md\n"
        "< Paste full artifact markdown content here >\n"
        "```\n"
    )

    return f"{system_content}{user_content}"


# endregion Template Prompts
