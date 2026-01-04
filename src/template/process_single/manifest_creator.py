import json
from ...config.pkg_config import PkgConfig
from ..front_mater_meta import FrontMatterMeta
from ...util import sha


class ManifestCreator:
    def __init__(self, build_number: int):
        self.config = PkgConfig()
        self.build_number = build_number

    def _get_manifest_data(self, templates: dict[str, FrontMatterMeta]) -> dict:
        manifest_data = {}
        for template_type, fm in templates.items():
            tr = fm.frontmatter.get("template_registry", {})
            tr_filename = tr.get("filename", "")
            if not tr_filename:
                raise ValueError(
                    f"Template registry filename missing for template type: {template_type}"
                )
            tr_path = fm.file_path.parent / tr_filename
            if not tr_path.exists():
                raise FileNotFoundError(
                    f"Template registry file not found: {tr_path} for template type: {template_type}"
                )
            tr_hash = sha.compute_file_sha256(tr_path)
            md_hash = sha.compute_file_sha256(fm.file_path)
            manifest_data[template_type] = {
                "template_file": fm.file_path.name,
                "template_version": fm.template_version,
                "template_family": fm.template_family,
                "template_hash": fm.sha256,
                "template_file_hash": md_hash,
                "registry_file_hash": tr_hash,
                "registry_file": tr_filename,
            }
        return manifest_data

    def create_manifest(self, templates: dict[str, FrontMatterMeta]) -> None:
        manifest_data = self._get_manifest_data(templates)
        manifest_path = (
            self.config.config_cache.get_dist_single(self.build_number)
            / "manifest.json"
        )
        manifest_dict = {
            "package_version": self.config.version,
            "build_number": self.build_number,
            "template_count": len(templates),
            "templates": manifest_data,
        }
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest_dict, f, indent=4)
