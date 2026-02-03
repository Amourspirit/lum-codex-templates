from pathlib import Path
from src.config.pkg_config import PkgConfig
from api.models.templates.templates_versions import TemplatesVersions
from functools import lru_cache


def _get_base_path() -> Path:
    config = PkgConfig()
    return config.config_cache.get_api_templates_path()
    # base_path = (
    #     config.root_path
    #     / config.api_info.base_dir
    #     / config.api_info.info_templates.dir_name  # codex-templates
    # )
    # return base_path


@lru_cache()
def get_available_versions() -> TemplatesVersions:
    """
    Scan the codex-templates directory and return a dictionary mapping
    each template subfolder name to a list of its version subfolder names
    (without the 'v' prefix), sorted in descending order.
    """
    base_path = _get_base_path()
    if not base_path.exists() or not base_path.is_dir():
        raise FileNotFoundError(f"Base path does not exist: {base_path}")

    available_versions: dict[str, list[str]] = {}
    for subfolder in sorted(base_path.iterdir()):
        if subfolder.is_dir():
            template_name = subfolder.name
            versions = []
            for version_folder in subfolder.iterdir():
                if version_folder.is_dir() and version_folder.name.startswith("v"):
                    # Strip 'v' and validate as version
                    version_str = version_folder.name[1:]  # Remove 'v'
                    try:
                        # Basic validation: split by '.' and check if all parts are digits
                        parts = version_str.split(".")
                        if len(parts) >= 2 and all(part.isdigit() for part in parts):
                            versions.append(version_str)
                    except ValueError:
                        continue  # Skip invalid version folders
            # Sort versions descending (highest first)
            versions.sort(key=lambda v: [int(x) for x in v.split(".")], reverse=True)
            if versions:  # Only include if there are versions
                available_versions[template_name] = versions
    templates_versions = TemplatesVersions(templates={})
    for template_key, versions in available_versions.items():
        templates_versions.add_entry(
            template_key=template_key,
            type=template_key,
            versions=versions,
        )
    return templates_versions


def get_available_template_types() -> list[str]:
    """
    Retrieves a list of all available template types.
    This function scans the available versions and extracts the unique keys
    representing the different types of templates supported.
    Returns:
        list[str]: A list of strings identifying the available template types.
    """

    versions = get_available_versions()
    return sorted(versions.templates.keys())


def get_latest_version_for_template(template_type: str) -> str | None:
    """
    Retrieves the latest version string for a given template type.
    Args:
        template_type (str): The type of the template for which to get the latest version.
    Returns:
        str | None: The latest version string if available, otherwise None.
    """
    versions = get_available_versions()
    template_entry = versions.templates.get(template_type)
    if template_entry and template_entry.versions:
        return template_entry.versions[0]  # Return the highest version
    return None
