import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
import yaml

# import json
from .builderbase import BuilderBase
from ..template.main_registery import MainRegistry
from ..template.front_mater_meta import FrontMatterMeta
from ..template.process.process_obsidian_templates import ProcessObsidianTemplates


class DefaultBuilder(BuilderBase):
    def __init__(self, build_version: str):
        super().__init__()
        self._build_version = build_version
        self._main_registry = MainRegistry()
        self._destination_path = self.config.root_path / self.config.pkg_out_dir
        self._destination_path.mkdir(parents=True, exist_ok=True)

    def _build_lockfile(self):
        batch_hash = self.compute_time_hash()
        lockfile = {
            "package_version": self._build_version,
            "batch_uid": f"{self.config.batch_prefix}-{self._build_version}-{batch_hash}",
            "batch_hash": batch_hash,
            "lockfile_version": self._build_version,
            "registry_version": self._main_registry.reg_version,
            "builder_version": self.config.version,
            "generated_at": datetime.now().astimezone().isoformat(),
            "strict_field_mode": self.config.strict_field_mode,
            "force_invalidate_previous": self.config.force_invalidate_previous,
            "auto_invoke_protocol_scroll": f"{self.config.auto_invoke_scroll}-{self._build_version}.md",
            "strict_hash_mode": self.config.strict_hash_mode,
            "registry_sources": {
                "registry_id": self._main_registry.reg_id,
                "name": self._main_registry.reg_name,
                "path": self._main_registry.file_name,
                "version": self._main_registry.reg_version,
                "format": "yaml",
                "enforced": True,
                "sha256": self.compute_sha256(self._main_registry.reg_path),
            },
            "categories": [],
        }
        return lockfile

    def _build_lockfile_categories(
        self, file_path: Path, fm: FrontMatterMeta, categories_map: dict
    ) -> None:
        template_meta = {
            "template_name": fm.template_name,
            "template_id": fm.template_id,
            "template_category": fm.template_category,
            "template_type": fm.template_type,
            "template_version": fm.template_version,
            "path": f"./{file_path.name}",
            "sha256": self.compute_sha256(file_path),
            "fields": fm.get_keys(),
        }

        # Group by fm.template_category
        cat_key = (
            fm.template_category.lower() if fm.template_category else "uncategorized"
        )
        if cat_key not in categories_map:
            categories_map[cat_key] = {
                "category": cat_key,
                "templates": [],
            }
        categories_map[cat_key]["templates"].append(template_meta)

    def build_package(self):
        # === Initialize Lockfile ===
        lockfile = self._build_lockfile()

        # === Paths ===
        output_zip_name = f"{self.config.package_output_name}-{self._build_version}.zip"
        output_zip_path = self._destination_path / output_zip_name
        if output_zip_path.exists():
            output_zip_path.unlink()

        lock_file_name = f"{self.config.lock_file_name}-{self._build_version}{self.config.lock_file_ext}"
        lockfile_path = self._destination_path / lock_file_name
        if lockfile_path.exists():
            lockfile_path.unlink()

        # === Create ZIP and Lockfile Metadata ===
        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Dictionary to group templates by category dynamically
            categories_map = {}
            processs_templates = ProcessObsidianTemplates()
            with processs_templates.process(
                {
                    "declared_registry_id": self._main_registry.reg_id,
                    "declared_registry_version": self._main_registry.reg_version,
                    "mapped_registry": self._main_registry.reg_id,
                    "mapped_registry_minimum_version": self._main_registry.reg_version,
                }
            ) as processed_template_paths:
                for file_path in processed_template_paths:
                    fm = FrontMatterMeta(file_path)
                    if not fm.has_field("template_id"):
                        continue

                    zipf.write(file_path, arcname=file_path.name)

                    # Build lockfile categories and templates
                    self._build_lockfile_categories(file_path, fm, categories_map)

                    # Convert map back to list for lockfile
                    lockfile["categories"] = list(categories_map.values())
                with tempfile.TemporaryDirectory() as tmp_dir:
                    temp_lockfile = Path(tmp_dir) / lock_file_name
                    with open(temp_lockfile, "w") as lockfile_f:
                        yaml.dump(
                            lockfile, lockfile_f, Dumper=yaml.Dumper, sort_keys=False
                        )
                    zipf.write(temp_lockfile, arcname=lock_file_name)

        # === Write Lockfile ===
        # with open(lockfile_path, "w") as lockfile_f:
        #     yaml.dump(lockfile, lockfile_f, Dumper=yaml.Dumper, sort_keys=False)
        # with open(lockfile_path.with_suffix(".json"), "w") as lockfile_json_f:
        #     json.dump(lockfile, lockfile_json_f, indent=4)
