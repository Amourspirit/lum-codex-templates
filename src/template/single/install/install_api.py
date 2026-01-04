from datetime import datetime
import json
import yaml

from ...front_mater_meta import FrontMatterMeta
from ....config.pkg_config import PkgConfig
from ....builder.build_ver_mgr import BuildVerMgr


class InstallAPI:
    def __init__(self, build_number: int = 0):
        self.config = PkgConfig()
        if build_number == 0:
            build_number = self._get_current_build_number()
        self.build_number = build_number
        self._build_dir_ensured = False
        self._src_dir = self.config.config_cache.get_dist_single(self.build_number)
        self._manifest = self._get_manifest()

    def _get_current_build_number(self) -> int:
        bvm = BuildVerMgr()
        return bvm.get_saved_version()

    def _get_manifest(self) -> dict:
        self._ensure_build_dir()
        manifest_path = self._src_dir / "manifest.json"

        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        return manifest_data

    def _ensure_build_dir(self) -> None:
        if self._build_dir_ensured:
            return
        build_dir = self.config.config_cache.get_dist_single(self.build_number)
        if not build_dir.exists():
            raise FileNotFoundError(f"Build directory does not exist: {build_dir}")
        self._build_dir_ensured = True

    def _load_template_file(self, template_type: str) -> FrontMatterMeta:
        if template_type not in self._manifest["templates"]:
            raise ValueError(
                f"Template type '{template_type}' not found in manifest for build {self.build_number}"
            )
        template_info = self._manifest["templates"][template_type]
        template_file = template_info["template_file"]
        template_path = self._src_dir / template_file
        if not template_path.exists():
            raise FileNotFoundError(
                f"Template file '{template_file}' not found in {self._src_dir}"
            )
        fm_meta = FrontMatterMeta(file_path=template_path)
        return fm_meta

    def _load_registry_file(self, template_type: str) -> dict:
        if template_type not in self._manifest["templates"]:
            raise ValueError(
                f"Template type '{template_type}' not found in manifest for build {self._src_dir}"
            )
        template_info = self._manifest["templates"][template_type]
        registry_file = template_info["registry_file"]
        registry_path = self._src_dir / registry_file
        if not registry_path.exists():
            raise FileNotFoundError(
                f"Registry file '{registry_file}' not found in {self._src_dir}"
            )
        with registry_path.open("r", encoding="utf-8") as f:
            registry_data = yaml.safe_load(f)
        return registry_data

    def _get_template_manifest(self, fm: FrontMatterMeta) -> dict:
        dt = datetime.now().astimezone()
        current_date = dt.isoformat()
        manifest = {
            "template_file": fm.file_path.name,
            "registry_file": "registry.json",
            "template_type": fm.template_type,
            "version": fm.template_version,
            "hash": fm.sha256,
            "template_hash": fm.sha256,
            "registry_id": fm.frontmatter.get("template_registry", {}).get(
                "registry_id", ""
            ),
            "status": "active",
            "requires_field_being": True,
            "installed_at": current_date,
        }
        if fm.template_id:
            manifest["template_id"] = fm.template_id
        return manifest

    def _update_template_frontmatter(self, fm: FrontMatterMeta) -> None:
        fm.set_field("template_filename", "template.md")
        fm.frontmatter["template_registry"]["filename"] = "registry.json"
        tp = self.config.config_cache.get_api_templates_path()
        tp_fm_dir = tp / f"{fm.template_type}" / f"v{fm.template_version}"
        # if not tp_fm_dir.exists():
        #     tp_fm_dir.mkdir(parents=True, exist_ok=True)
        fm.file_path = tp_fm_dir / "template.md"
        fm.recompute_sha256()

    def _update_registry_data(self, fm: FrontMatterMeta, registry_data: dict) -> None:
        registry_data["template_filename"] = "template.md"
        registry_data["template_hash"] = fm.sha256

    def install_single(self, template_type: str) -> None:
        if template_type not in self._manifest["templates"]:
            raise ValueError(
                f"Template type '{template_type}' not found in manifest for build {self._src_dir}"
            )
        fm = self._load_template_file(template_type)
        registry = self._load_registry_file(template_type)
        self._update_template_frontmatter(fm)
        self._update_registry_data(fm, registry)
        manifest = self._get_template_manifest(fm)
        dest_path = fm.file_path.parent
        if not dest_path.exists():
            dest_path.mkdir(parents=True, exist_ok=True)

        print(f"Installing template '{template_type}' to {dest_path}")

        fm.write_template(fm.file_path)
        registry_path = dest_path / "registry.json"
        with registry_path.open("w", encoding="utf-8") as f:
            # yaml.dump(registry, f, sort_keys=False)
            json.dump(registry, f, indent=4)
        with (dest_path / "manifest.json").open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=4)

    def install(self) -> None:
        # Implementation of the install method
        for template_type in self._manifest["templates"].keys():
            self.install_single(template_type)
