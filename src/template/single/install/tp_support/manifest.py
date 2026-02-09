from datetime import datetime
from src.template.front_mater_meta import FrontMatterMeta
from src.config.pkg_config import PkgConfig

MANIFEST_VERSION = "0.1.0"


def get_manifest(fm: FrontMatterMeta) -> dict:

    config = PkgConfig()
    dt = datetime.now().astimezone()
    current_date = dt.isoformat()

    registry_id = fm.frontmatter.get("template_registry", {}).get("registry_id", "")

    data = {
        "name": f"template_manifest_{fm.template_type}",
        "version": MANIFEST_VERSION,
        "description": f"manifest for version {fm.template_version} for template type {fm.template_type}",
        "template_info": {
            "template_type": fm.template_type,
            "template_file": fm.file_path.name,
            "version": fm.template_version,
            "hash": fm.sha256,
            "template_hash": fm.sha256,
            "template_hash_algorithm": "sha256",
            "status": "available",
            "requires_field_being": True,
        },
        "registry_info": {
            "registry_id": registry_id,
            "registry_file": "registry.json",
        },
        "instructions_info": {
            "instructions_file": "instructions.md",
        },
        "installed_at": current_date,
        "canonical_mode": {
            "version": config.template_ceib_api.version,
            "executor_mode": config.template_ceib_api.executor_mode,
        },
    }
    if fm.template_id:
        data["template_info"]["template_id"] = fm.template_id
    return data
