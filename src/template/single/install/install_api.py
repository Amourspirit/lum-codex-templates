from datetime import datetime
import json
from typing import Any
from pathlib import Path
import yaml

from ...front_mater_meta import FrontMatterMeta
from ....config.pkg_config import PkgConfig
from ....builder.build_ver_mgr import BuildVerMgr
from .tp_support.instructions import Instructions
from .tp_support.cbib import CBIB
from ...main_registry import MainRegistry
from ...process.process_obsidian_templates import ProcessObsidianTemplates


class InstallAPI:
    def __init__(self, build_number: int = 0):
        self._cache = {}
        self.config = PkgConfig()
        if build_number == 0:
            build_number = self._get_current_build_number()
        self.build_number = build_number
        self._build_dir_ensured = False
        self._src_dir = self.config.config_cache.get_dist_single(self.build_number)
        self._manifest = self._get_manifest()
        self._instructions = Instructions()
        self._cbib = CBIB()
        self._main_registry = MainRegistry(build_version=self.build_number)
        self._original_templates = self._get_original_templates()

    def _get_original_templates(self) -> dict[str, FrontMatterMeta]:
        process_templates = ProcessObsidianTemplates()
        processed_template_data = process_templates.process(
            {
                "declared_registry_id": self._main_registry.reg_id,
                "declared_registry_version": self._main_registry.reg_version,
                "mapped_registry": self._main_registry.reg_id,
                "mapped_registry_minimum_version": self._main_registry.reg_version,
                "batch_number": str(self.build_number),
            }
        )
        results = {}
        for fm in processed_template_data.values():
            results[fm.template_type] = fm
        return results

    def _get_current_build_number(self) -> int:
        bvm = BuildVerMgr()
        return bvm.get_saved_version()

    def _get_manifest(self) -> dict[str, Any]:
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
            "registry_file": "registry.json",
            "template_file": fm.file_path.name,
            "template_type": fm.template_type,
            "template_hash_algorithm": "sha256",
            "version": fm.template_version,
            "hash": fm.sha256,
            "template_hash": fm.sha256,
            "registry_id": fm.frontmatter.get("template_registry", {}).get(
                "registry_id", ""
            ),
            "canonical_mode": {
                "version": self.config.template_ceib_api.version,
                "executor_mode": self.config.template_ceib_api.executor_mode,
            },
            "status": "available",
            "requires_field_being": True,
            "installed_at": current_date,
            "instructions_file": "instructions.md",
        }
        if fm.template_id:
            manifest["template_id"] = fm.template_id
        return manifest

    def _generate_instructions(
        self, fm: FrontMatterMeta, registry: dict
    ) -> FrontMatterMeta:
        result = self._instructions.generate_front_matter(fm=fm, registry=registry)
        return result

    def _generate_frontmatter_instructions(
        self, fm: FrontMatterMeta, registry: dict, dest_path: Path
    ) -> FrontMatterMeta:
        generated_fm = self._generate_instructions(fm=fm, registry=registry)
        dest_file = dest_path / "instructions.md"
        generated_fm.file_path = dest_file
        return generated_fm

    def _update_template_frontmatter(self, fm: FrontMatterMeta) -> None:
        orig_tp = self._original_templates.get(fm.template_type)
        if not orig_tp:
            raise ValueError(
                f"Original template data not found for type '{fm.template_type}'"
            )
        if not fm.template_id:
            fm.template_id = orig_tp.template_id
        for field in self.config.template_config.api_installer_template_cleanup_fields:
            if fm.has_field(field):
                fm.remove_field(field)
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
        if fm.template_id:
            registry_data["template_id"] = fm.template_id

    def _ensure_cbib(self) -> None:
        key = "cbib_ensured"
        if key in self._cache:
            return
        cbib_data = self._cbib.get_cbib()
        version = cbib_data["version"]
        cbib_path = self.config.config_cache.get_api_cbib_path() / f"v{version}"
        if not cbib_path.exists():
            cbib_path.mkdir(parents=True, exist_ok=True)
        cbib_file = cbib_path / "cbib.json"
        if cbib_file.exists():
            self._cache[key] = True
            return
        with cbib_file.open("w", encoding="utf-8") as f:
            json.dump(cbib_data, f, indent=4)
        self._cbib.write_model_to_file()
        self._cache[key] = True

    def _get_sorted_registry(self, registry: dict) -> dict:
        sort_order_identity = [
            "registry_id",
            "registry_version",
            "template_id",
        ]
        sort_order_structural = [
            "template_type",
            "template_version",
            "template_filename",
            "template_hash",
            "template_strict_integrity",
            "template_hash_enforcement",
            "audit",
            "placeholder_rules",
            "autofill",
            "conditionals",
            "invocation_agents",
        ]
        sort_order_execution = [
            "canonical_mode",
            "fail_on_unknown_field",
            "fail_on_unresolved_field_placeholder",
            "allow_prompt_placeholders",
            "allow_inference",
            "fail_on_field_mismatch",
            "render_contract",
        ]
        cp = registry.copy()
        sorted_registry = {}
        for key in sort_order_identity + sort_order_structural + sort_order_execution:
            if key in cp:
                sorted_registry[key] = cp.pop(key)
        sorted_registry.update(cp)
        return sorted_registry

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

        instructions_md = self._generate_frontmatter_instructions(
            fm=fm, registry=registry, dest_path=dest_path
        )
        self._ensure_cbib()
        print(f"Installing template '{template_type}' to {dest_path}")

        fm.write_template(fm.file_path)
        registry_path = dest_path / "registry.json"
        sorted_registry = self._get_sorted_registry(registry)
        with registry_path.open("w", encoding="utf-8") as f:
            # yaml.dump(registry, f, sort_keys=False)
            json.dump(sorted_registry, f, indent=4)
        with (dest_path / "manifest.json").open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=4)
        instructions_md.write_template(instructions_md.file_path)

    def install(self) -> None:
        # Implementation of the install method
        for template_type in self._manifest["templates"].keys():
            self.install_single(template_type)
