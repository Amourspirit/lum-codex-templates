import uuid
from collections import defaultdict

# from urllib.parse import quote
from ..util.result import Result
from api.lib.exceptions import (
    VersionError,
    VersionLatestError,
    VersionEmptyError,
    VersionFormatError,
    VersionNoneError,
)


def validate_version_str(
    version: str | None,
) -> Result[str, None] | Result[None, VersionError]:
    if version is None:
        return Result(None, VersionNoneError("Version cannot be None."))
    if not version:
        return Result(None, VersionEmptyError("Version cannot be empty."))
    v = version.strip().lower()
    if v == "latest":
        return Result(None, VersionLatestError("Version 'latest' is not allowed here."))
    v = v.lstrip("v")
    if not v:
        return Result(None, VersionEmptyError("Version cannot be empty."))
    if not v.replace(".", "").isdigit():
        return Result(None, VersionFormatError("Invalid version format."))
    if v.isdigit():
        v = f"{v}.0"
    if not v.startswith("v"):
        v = "v" + v
    return Result(v, None)


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

    v_result = validate_version_str(version)
    if not Result.is_success(v_result):
        raise v_result.error
    ver = v_result.data
    a_name = artifact_name if artifact_name else ""

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
    input2 = McpToolArg(name="input_ver", value=McpToolArg(name="version", value=ver))
    input3 = McpToolArg(
        name="input_artifact_name",
        value=McpToolArg(name="name", value=a_name),
    )
    tool = McpTool(tool_name="get_codex_template", tool_args=[input1, input2, input3])
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
    input2 = McpToolArg(name="input_ver", value=McpToolArg(name="version", value=ver))

    input3 = McpToolArg(
        name="input_artifact_name",
        value=McpToolArg(name="name", value=a_name),
    )
    tool_args = [input1, input2, input3]
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
    input2 = McpToolArg(name="input_ver", value=McpToolArg(name="version", value=ver))
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
    input2 = McpToolArg(name="input_ver", value=McpToolArg(name="version", value=ver))
    input3 = McpToolArg(
        name="input_artifact_name",
        value=McpToolArg(name="name", value=a_name),
    )
    tool = McpTool(
        tool_name="get_codex_template_manifest", tool_args=[input1, input2, input3]
    )
    mcp_paths["manifest_tool"] = tool

    return mcp_paths


def get_mcp_tool_call_rpc(
    template_type: str,
    version: str,
    artifact_name: str | None = None,
) -> dict:
    """
    Generate MCP (Model Context Protocol) tool call RPC requests for template operations.
    Creates a dictionary containing four JSON-RPC 2.0 formatted tool call requests:
    - template_tool: Retrieves the codex template
    - instructions_tool: Retrieves the codex template instructions
    - registry_tool: Retrieves the codex template registry
    - manifest_tool: Retrieves the codex template manifest
    Args:
        template_type (str): The type of template to retrieve.
        version (str): The version of the template. Must be a valid version string.
        artifact_name (str | None, optional): The name of a specific artifact to include
            in the instructions tool call. Defaults to None.
    Returns:
        dict: A dictionary with keys 'template_tool', 'instructions_tool',
            'registry_tool', and 'manifest_tool', each containing a JSON-RPC 2.0
            formatted tool call object with unique call IDs.
    Raises:
        Exception: If the version string validation fails, the validation error is raised.
    """

    results = {}
    # generate a uuid
    v_result = validate_version_str(version)
    if not Result.is_success(v_result):
        raise v_result.error
    ver = v_result.data
    call_id = str(uuid.uuid4())
    a_name = artifact_name if artifact_name else ""
    results["template_tool"] = {
        "jsonrpc": "2.0",
        "id": call_id,
        "method": "tools/call",
        "params": {
            "name": "get_codex_template",
            "arguments": {
                "input_type": {"type": template_type},
                "input_ver": {"version": ver},
                "input_artifact_name": {"name": a_name},
            },
        },
    }

    call_id = str(uuid.uuid4())
    results["instructions_tool"] = {
        "jsonrpc": "2.0",
        "id": call_id,
        "method": "tools/call",
        "params": {
            "name": "get_codex_template_instructions",
            "arguments": {
                "input_type": {"type": template_type},
                "input_ver": {"version": ver},
                "input_artifact_name": {"name": a_name},
            },
        },
    }

    call_id = str(uuid.uuid4())
    results["registry_tool"] = {
        "jsonrpc": "2.0",
        "id": call_id,
        "method": "tools/call",
        "params": {
            "name": "get_codex_template_registry",
            "arguments": {
                "input_type": {"type": template_type},
                "input_ver": {"version": ver},
            },
        },
    }

    call_id = str(uuid.uuid4())
    results["manifest_tool"] = {
        "jsonrpc": "2.0",
        "id": call_id,
        "method": "tools/call",
        "params": {
            "name": "get_codex_template_manifest",
            "arguments": {
                "input_type": {"type": template_type},
                "input_ver": {"version": ver},
                "input_artifact_name": {"name": a_name},
            },
        },
    }

    return results


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
    v_result = validate_version_str(version)
    if not Result.is_success(v_result):
        raise v_result.error
    ver = v_result.data
    input = McpToolArg(name="version", value=ver)
    return McpTool(tool_name="get_canonical_executor_mode", tool_args=[input])


def get_mcp_executor_mode_rpc(version: str) -> dict:
    """
    Generate a JSON-RPC 2.0 request payload to retrieve the canonical executor mode for a given version.
    This function creates a structured RPC call that invokes the 'get_canonical_executor_mode' tool
    with the provided version string. The version is first validated before being included in the request.
    Args:
        version (str): The version string to validate and retrieve executor mode for.
    Returns:
        dict: A dictionary containing the JSON-RPC 2.0 request with the following structure:
            {
                "template_tool": {
                    "id": <uuid>,
                            "input_ver": {"version": <validated_version>}
    Raises:
        Exception: If the version string validation fails, raises the error from the validation result.
    Example:
        >>> result = get_mcp_executor_mode_rpc("v1.0")
        >>> result["template_tool"]["method"]
        'tools/call'
    """

    # http://localhost:8000/api/v1/executor_modes/CANONICAL-EXECUTOR-MODE?version=v1.0

    # generate a uuid
    v_result = validate_version_str(version)
    if not Result.is_success(v_result):
        raise v_result.error
    ver = v_result.data
    call_id = str(uuid.uuid4())
    return {
        "jsonrpc": "2.0",
        "id": call_id,
        "method": "tools/call",
        "params": {
            "name": "get_canonical_executor_mode",
            "arguments": {
                "version": ver,
            },
        },
    }
