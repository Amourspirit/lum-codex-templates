from collections import defaultdict
from functools import lru_cache
from src.config.pkg_config import PkgConfig
from urllib.parse import quote

_SETTINGS = PkgConfig()
_TEMPLATE_DIR = _SETTINGS.config_cache.get_api_templates_path()


class McpToolArg(defaultdict):
    name: str
    value: str


class McpTool(defaultdict):
    tool_name: str
    tool_args: list[McpToolArg]


class McpPaths(defaultdict):
    template_tool: McpTool
    instructions_tool: McpTool
    registry_tool: McpTool
    manifest_tool: McpTool


@lru_cache(maxsize=128)
def get_mcp_paths_template(
    template_type: str,
    version: str,
    artifact_name: str | None = None,
) -> McpPaths:
    """
    Generate MCP paths configuration for template-related tools.
    This function creates a structured collection of MCP (Model Context Protocol) tool
    configurations for accessing various template endpoints. It constructs tool arguments
    based on template type, version, and optional artifact name.
    Args:
        template_type (str): The type of template (e.g., 'stone', 'glyph').
        version (str): The version string for the template (e.g., 'v2.10').
        artifact_name (str | None, optional): The name of the artifact. Required for
            instructions tool, optional otherwise. Defaults to None.
    Returns:
        McpPaths: A dictionary-like object containing four MCP tools:
            - template_tool: Tool for fetching the template content
            - instructions_tool: Tool for fetching template instructions (includes
              artifact_name if provided)
            - registry_tool: Tool for fetching the template registry
            - manifest_tool: Tool for fetching the template manifest
    Example:
        >>> paths = get_mcp_paths_template('glyph', 'v2.11', 'My Artifact')
        >>> # Creates MCP tools for endpoints:
        >>> # - get_codex_template
        >>> # - get_codex_template_instructions (with artifact_name)
        >>> # - get_codex_template_registry
        >>> # - get_codex_template_manifest
    """

    mcp_paths = McpPaths()
    # # http://localhost:8000/api/v1/templates/glyph/template?artifact_name=My%20Artifact&version=v2.11
    # {
    #   "input_type": {
    #       "type": "stone"
    #   },
    #   "input_ver": {
    #       "version": "v2.10"
    #   }
    # }
    input1 = McpToolArg(
        name="input_type", value=McpToolArg(name="type", value=template_type)
    )
    input2 = McpToolArg(
        name="input_ver", value=McpToolArg(name="version", value=version)
    )
    tool = McpTool(tool_name="get_codex_template", tool_args=[input1, input2])
    mcp_paths["template_tool"] = tool

    # http://localhost:8000/api/v1/templates/glyph/instructions?artifact_name=My%20Artifact&version=v2.11
    # {
    #   "input_type": {
    #     "type": "stone"
    #   },
    #   "input_ver": {
    #     "version": "2.10"
    #   },
    #   "input_artifact_name": {
    #     "name": "My Artifact"
    #   }
    # }
    input1 = McpToolArg(
        name="input_type", value=McpToolArg(name="type", value=template_type)
    )
    input2 = McpToolArg(
        name="input_ver", value=McpToolArg(name="version", value=version)
    )

    tool_args = [input1, input2]
    if artifact_name:
        input3 = McpToolArg(
            name="input_artifact_name",
            value=McpToolArg(name="name", value=artifact_name),
        )
        tool_args.append(input3)
    tool = McpTool(tool_name="get_codex_template_instructions", tool_args=tool_args)
    mcp_paths["instructions_tool"] = tool

    # http://localhost:8000/api/v1/templates/glyph/registry?artifact_name=My%20Artifact&version=v2.11
    # {
    #   "input_type": {
    #       "type": "stone"
    #   },
    #   "input_ver": {
    #       "version": "v2.10"
    #   }
    # }
    input1 = McpToolArg(
        name="input_type", value=McpToolArg(name="type", value=template_type)
    )
    input2 = McpToolArg(
        name="input_ver", value=McpToolArg(name="version", value=version)
    )
    tool = McpTool(tool_name="get_codex_template_registry", tool_args=[input1, input2])
    mcp_paths["registry_tool"] = tool

    # http://localhost:8000/api/v1/templates/glyph/manifest?artifact_name=My%20Artifact&version=v2.11
    # {
    #   "input_type": {
    #       "type": "stone"
    #   },
    #   "input_ver": {
    #       "version": "v2.10"
    #   }
    # }
    input1 = McpToolArg(
        name="input_type", value=McpToolArg(name="type", value=template_type)
    )
    input2 = McpToolArg(
        name="input_ver", value=McpToolArg(name="version", value=version)
    )
    tool = McpTool(tool_name="get_codex_template_manifest", tool_args=[input1, input2])
    mcp_paths["manifest_tool"] = tool

    return mcp_paths


def get_mcp_executor_mode_tool(version: str) -> McpTool:
    """Create an MCP tool invocation for fetching the canonical executor mode by version.
    Args:
        version (str): API version string to request (e.g., "v1.0").
    Returns:
        McpTool: Tool configuration targeting "get_canonical_executor_mode" with
        nested arguments containing the version.
    """

    # http://localhost:8000/api/v1/executor_modes/CANONICAL-EXECUTOR-MODE?version=v1.0
    # {
    #   "version": "v1.0"
    # }
    input = McpToolArg(
        name="input_ver", value=McpToolArg(name="version", value=version)
    )
    return McpTool(tool_name="get_canonical_executor_mode", tool_args=[input])

def to_plain(obj) -> dict | list | str:
    """
    Convert nested defaultdict structures to plain Python dictionaries.
    This function recursively traverses an object and converts any defaultdict
    instances to regular dictionaries, while preserving lists and other types.
    Args:
        obj: The object to convert. Can be a defaultdict, dict, list, or any other type.
    Returns:
        A plain Python object with the same structure as the input, but with all
        defaultdict instances converted to regular dictionaries. Returns dict, list,
        or str depending on the input type.
    Examples:
        >>> from collections import defaultdict
        >>> dd = defaultdict(list)
        >>> dd['key'] = ['value']
        >>> to_plain(dd)
        {'key': ['value']}
        >>> nested = defaultdict(lambda: defaultdict(list))
        >>> nested['outer']['inner'] = ['item']
        >>> to_plain(nested)
        {'outer': {'inner': ['item']}}
    """

    if isinstance(obj, defaultdict):
        return {k: to_plain(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_plain(v) for v in obj]
    return obj