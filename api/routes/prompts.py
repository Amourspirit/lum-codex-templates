from loguru import logger
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from ..models.descope.descope_session import DescopeSession
from ..responses.markdown_response import MarkdownResponse
from ..lib.descope.session import get_descope_session
from ..lib.env import env_info
from ..lib.routes import fn_versions

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

    system_content = (
        "## System Instructions  \n\n"
        "**You are an assistant that can:**  \n"
        "- Call tools (e.g. `get_codex_template_instructions`) to perform active queries.\n"
        "- Load resources (URIs starting with `executor-mode://`) to read static documentation.\n"
        "\n"
        "**Available tools:**  \n"
        "  1. **get_codex_template(input_type: ArgTemplateType, input_ver: ArgTemplateVersionOptional)**\n"
        "    - Use this when you need to get the full template content for a specific type and version.\n"
        "  2. **get_codex_template_instructions(input_type: ArgTemplateType, input_ver: ArgTemplateVersionOptional, input_artifact_name: ArgArtifactNameOptional)**\n"
        "    - Use this when you need to get the instructions on how to apply templates.\n"
        "  3. **get_codex_template_registry(input_type: ArgTemplateType, input_ver: ArgTemplateVersionOptional)**\n"
        "    - Use this when you need to get the registry for the template. This registry determines how the metadata in the template is structured and the rules to apply.\n"
        "  4. **verify_codex_template_artifact(artifact_name: str, template_content: str)**\n"
        "    - Use this to verify the metadata fields of a template artifact against the registered schema.\n"
        "    - Input `template_content` should include the full markdown content with frontmatter.\n"
        "  5. **finalize_codex_template_artifact(artifact_name: str, template_content: str)**\n"
        "    - Use this to finalize an artifact submission by validating and cleaning its metadata.\n"
        "    - Input `template_content` should include the full markdown content with frontmatter.\n"
        "\n\n"
        "## Available resources:  \n"
        "  1. `executor-mode://default_executor_mode`\n"
        "    - Executor mode used when applying templates.\n"
    )

    user_content = (
        "## User Instructions  \n\n"
        f"Upgrade the artifact named '{artifact_name}' to the latest template of type `{tt}` and version '{latest_version}'.  \n"
        f'  1. Call tool `get_codex_template({{"input_type":{{"type":"{tt}"}},"input_ver":{{"version":"{latest_version}"}}}})` to get the full template content.\n'
        "    - This is the target template to upgrade to.\n"
        "  2. Use the resource `executor-mode://default_executor_mode` to understand the executor mode to apply the template.\n"
        f'  3. Call tool `get_codex_template_registry({{"input_type":{{"type":"{tt}"}},"input_ver":{{"version":"{latest_version}"}}}})` to get the template registry.\n'
        "    - Use this registry to understand the structure and rules for the template metadata.\n"
        f'  4. Call tool `get_codex_template_instructions({{"input_type":{{"type":"{tt}"}},"input_ver":{{"version":"{latest_version}"}},"input_artifact_name":{{"name":"{artifact_name}"}}}})` to get the instructions for applying the template.\n'
        "    - Use these instructions to guide the upgrade process.\n"
        "\n"
        "Proceed to upgrade the artifact by applying the template according to the instructions and registry rules.\n"
        "Now that the the upgrade is complete, it is time to verify and finalize the upgraded artifact.\n"
        "\n"
        "4. Pass the upgraded template content, including the full markdown content with frontmatter, to `verify_codex_template_artifact` tool to verify the metadata fields.\n"
        "5. Next, pass the verified template content to `finalize_codex_template_artifact` tool to finalize the artifact submission.\n"
        "6. Provide the finalized artifact as the output."
    )

    return f"{system_content}\n\n{user_content}"


# endregion Template Prompts
