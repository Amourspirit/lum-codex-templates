from collections import defaultdict
from functools import lru_cache
from src.config.pkg_config import PkgConfig
from urllib.parse import quote

_SETTINGS = PkgConfig()
_TEMPLATE_DIR = _SETTINGS.config_cache.get_api_templates_path()


class ApiPaths(defaultdict):
    template_api_path: str
    instructions_api_path: str
    registry_api_path: str
    manifest_api_path: str


@lru_cache(maxsize=128)
def get_api_paths_template(
    template_type: str,
    version: str,
    app_root_url: str,
    artifact_name: str | None = None,
) -> ApiPaths:
    """
    Build API endpoint URLs for a template resource and return them in an ApiPaths mapping.
    Args:
        template_type: Template category segment used in the path (e.g., "glyph").
        version: Version query parameter (e.g., "v2.11").
        app_root_url: Base application URL (e.g., "http://localhost:8000/api/v1").
        artifact_name: Optional artifact name to include as a URL-encoded query parameter.
    Returns:
        ApiPaths: Mapping containing template, instructions, registry, and manifest URLs.
    """

    api_paths = ApiPaths()
    # # http://localhost:8000/api/v1/templates/glyph/template?artifact_name=My%20Artifact&version=v2.11
    api_path = f"{app_root_url}/{_TEMPLATE_DIR.name}/{template_type}/template?version={version}"
    if artifact_name:
        api_path += f"&artifact_name={quote(artifact_name)}"
    api_paths["template_api_path"] = api_path

    # http://localhost:8000/api/v1/templates/glyph/instructions?artifact_name=My%20Artifact&version=v2.11
    api_path = f"{app_root_url}/{_TEMPLATE_DIR.name}/{template_type}/instructions?version={version}"
    if artifact_name:
        api_path += f"&artifact_name={quote(artifact_name)}"
    api_paths["instructions_api_path"] = api_path

    # http://localhost:8000/api/v1/templates/glyph/registry?artifact_name=My%20Artifact&version=v2.11
    api_path = f"{app_root_url}/{_TEMPLATE_DIR.name}/{template_type}/registry?version={version}"
    if artifact_name:
        api_path += f"&artifact_name={quote(artifact_name)}"
    api_paths["registry_api_path"] = api_path

    # http://localhost:8000/api/v1/templates/glyph/manifest?artifact_name=My%20Artifact&version=v2.11
    api_path = f"{app_root_url}/{_TEMPLATE_DIR.name}/{template_type}/manifest?version={version}"
    if artifact_name:
        api_path += f"&artifact_name={quote(artifact_name)}"
    api_paths["manifest_api_path"] = api_path

    return api_paths


def get_api_path_executor_mode(
    version: str,
    app_root_url: str,
) -> str:
    """
    Build the executor mode API path for the canonical executor mode.
    Args:
        version: API version query parameter to include in the URL.
        app_root_url: Base application URL (e.g., http://localhost:8000/api/v1).
    Returns:
        Fully qualified API path to the canonical executor mode endpoint.
    """

    # http://localhost:8000/api/v1/executor_modes/CANONICAL-EXECUTOR-MODE?version=v1.0
    api_path = (
        f"{app_root_url}/executor_modes/CANONICAL-EXECUTOR-MODE?version={version}"
    )

    return api_path
