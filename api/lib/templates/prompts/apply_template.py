import json
from loguru import logger
from jinja2 import Template
from src.config.pkg_config import PkgConfig
from api.lib.routes import mcp_path
from api.lib.routes.fn_versions import get_latest_version_for_template

_SETTINGS = PkgConfig()


def _get_apply_template_prompt(
    template_type: str,
    artifact_name: str,
    template_name: str,
    attached_img_name: str | None = None,
):
    """
    Gets a structured prompt for applying an artifact to the latest version of a specified template type. The prompt includes instructions, template content, and registry information to guide the application process.

    Args:
        template_type (str): The type of the template to apply to (e.g. `glyph`, `sigil`, `seal`).
        artifact_name (str): The name of the artifact to apply.
        attached_img_name (str, optional): Optional name such as `Glyph` or `Sigil` of an attached image to be included in the prompt.
        template_name (str): Name of the template.

    Raises:
        ValueError: If the template type is invalid or if no versions are found for the specified template type.
    Returns:
        str: A structured prompt in markdown format for applying the artifact to the latest version of the specified template type.
    """

    api_path = _SETTINGS.config_cache.get_api_path()

    if not template_name.endswith(".md"):
        template_name += ".md"

    template_file_path = api_path / "templates" / "prompts" / template_name
    if not template_file_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_file_path}")

    tt = template_type.strip().lower()
    if not tt:
        raise ValueError("Template type must be a non-empty string.")

    try:
        latest_version = get_latest_version_for_template(template_type)
        if not latest_version:
            logger.error(f"No versions found for template type '{tt}'.")
            raise ValueError(f"No versions found for template type '{tt}'.")
        logger.debug(
            "No version specified. Using latest version: {version}",
            version=latest_version,
        )
    except ValueError as e:
        logger.error(str(e))
        raise e

    tool_rpcs = mcp_path.get_mcp_tool_call_rpc(
        template_type=tt, version=latest_version, artifact_name=artifact_name
    )

    template_tool = tool_rpcs["template_tool"]
    instructions_tool = tool_rpcs["instructions_tool"]
    registry_tool = tool_rpcs["registry_tool"]
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

    raw_content = template_file_path.read_text()

    template: Template = Template(source=raw_content)

    content = template.render(
        get_codex_template=template_tool["params"]["name"],
        get_codex_template_instructions=instructions_tool["params"]["name"],
        get_codex_template_registry=registry_tool["params"]["name"],
        get_canonical_executor_mode=executor_mode_tool["params"]["name"],
        verify_codex_template_artifact=verify_tool["params"]["name"],
        finalize_codex_template_artifact=finalize_tool["params"]["name"],
        artifact_name=artifact_name,
        template_type=tt,
        template_version=ver,
        json_template=template_tool_json,
        json_instructions=instructions_tool_json,
        json_registry=registry_tool_json,
        json_cbib=executor_mode_tool_json,
        json_verify=verify_tool_json,
        json_final=finalize_tool_json,
        attached_img_name=attached_img_name,
        template_content_placeholder=template_content_placeholder,
    )
    return content


def get_apply_template_prompt(
    template_type: str,
    artifact_name: str,
    attached_img_name: str | None = None,
    template_name: str | None = None,
):
    """
    Gets a structured prompt for applying an artifact to the latest version of a specified template type. The prompt includes instructions, template content, and registry information to guide the application process.

    Args:
        template_type (str): The type of the template to apply to (e.g. `glyph`, `sigil`, `seal`).
        artifact_name (str): The name of the artifact to apply.
        attached_img_name (str, optional): Optional name such as `Glyph` or `Sigil` of an attached image to be included in the prompt.
        template_name (str, optional): Optional name of the template such as `apply_01.md`.

    Raises:
        ValueError: If the template type is invalid or if no versions are found for the specified template type.
    Returns:
        str: A structured prompt in markdown format for applying the artifact to the latest version of the specified template type.
    """

    if not template_name:
        template_name = "apply_01.md"
    return _get_apply_template_prompt(
        template_type=template_type,
        artifact_name=artifact_name,
        attached_img_name=attached_img_name,
        template_name=template_name,
    )


def get_upgrade_template_prompt(
    template_type: str,
    artifact_name: str,
    attached_img_name: str | None = None,
    template_name: str | None = None,
):
    """
    Gets a structured prompt for upgrading an artifact to the latest version of a specified template type. The prompt includes instructions, template content, and registry information to guide the upgrade process.

    Args:
        template_type (str): The type of the template to upgrade to (e.g. `glyph`, `sigil`, `seal`).
        artifact_name (str): The name of the artifact to upgrade.
        attached_img_name (str, optional): Optional name such as `Glyph` or `Sigil` of an attached image to be included in the prompt.
        template_name (str, optional): Optional name of the template such as `upgrade_01.md`.

    Raises:
        ValueError: If the template type is invalid or if no versions are found for the specified template type.
    Returns:
        str: A structured prompt in markdown format for upgrading the artifact to the latest version of the specified template type.
    """

    if not template_name:
        template_name = "upgrade_01.md"
    return _get_apply_template_prompt(
        template_type=template_type,
        artifact_name=artifact_name,
        attached_img_name=attached_img_name,
        template_name=template_name,
    )
