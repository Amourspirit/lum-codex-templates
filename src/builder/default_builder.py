import zipfile
from datetime import datetime
from pathlib import Path
import yaml
from ..config.pkg_config import PkgConfig
from ..template.main_registery import MainRegistry


class DefaultBuilder:
    def __init__(self, build_version: str):
        self.config = PkgConfig()
        self._build_version = build_version
        self._main_registry = MainRegistry()

    def build_package(self):
        # === Initialize Lockfile ===
        lockfile = {
            "package_version": self._build_version,
            "lockfile_version": self._build_version,
            "registry_version": self._main_registry.reg_version,
            "builder_version": self.config.version,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "force_invalidate_previous": True,
            "auto_invoke_protocol_scroll": self.config.auto_invoke_scroll,
            "strict_hash_mode": True,
            "categories": [],
        }

        # === Paths ===
        output_zip_path = Path(self.config.output_zip)
        lockfile_path = Path(self.config.lockfile)

        # === Create ZIP and Lockfile Metadata ===
        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for dir_name in self.config.template_dirs:
                dir_path = Path(dir_name)
                if dir_path.exists() and dir_path.is_dir():
                    category_templates = {"category": dir_name.lower(), "templates": []}
                    for file_path in dir_path.glob("*.md"):
                        zipf.write(file_path, arcname=file_path.name)
                        template_meta = {
                            "template_name": file_path.stem,
                            "template_id": f"TEMPLATE-{file_path.stem.upper()}",
                            "template_category": dir_name.lower(),
                            "template_type": dir_name.lower(),
                            "template_version": "unknown",
                            "path": str(file_path),
                            "sha256": "uncomputed",  # To be added later
                            "fields": [
                                "template_id",
                                "template_type",
                                "template_category",
                                "template_name",
                            ],
                        }
                        category_templates["templates"].append(template_meta)
                    lockfile["categories"].append(category_templates)

        # === Write Lockfile ===
        with open(lockfile_path, "w") as lockfile_f:
            yaml.dump(lockfile, lockfile_f)
