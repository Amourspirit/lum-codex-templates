#!/usr/bin/env python3
from datetime import datetime
import os
import yaml
import argparse
from pathlib import Path
import zipfile

from src.config.pkg_config import PkgConfig

# === Configuration (could be externalized later) ===
# CONFIG = {
#     "PACKAGE_VERSION": "44",
#     "LOCKFILE": "codex-template-44.lock",
#     "README": "README.md",
#     "UPLOAD_SCROLL": "SCROLL-TEMPLATE-UPLOAD-44.md",
#     "INCLUDE_REGISTRY": True,
#     "REGISTRY_FILE": "00-Master_Metadata_Registry.yml",
#     "TEMPLATE_DIRS": ["Glyphs", "Seals", "Scrolls", "Certificate"],
#     "OUTPUT_ZIP": "codex-templates-44.zip"
# }


def main():
    config = PkgConfig()

    # === Initialize Lockfile ===
    lockfile = {
        "package_version": CONFIG["PACKAGE_VERSION"],
        "lockfile_version": "1",
        "registry_version": "2.5",
        "builder_version": "4.6",
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "force_invalidate_previous": True,
        "auto_invoke_protocol_scroll": CONFIG["UPLOAD_SCROLL"],
        "strict_hash_mode": True,
        "categories": [],
    }

    # === Paths ===
    output_zip_path = Path(CONFIG["OUTPUT_ZIP"])
    lockfile_path = Path(CONFIG["LOCKFILE"])

    # === Create ZIP and Lockfile Metadata ===
    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for dir_name in CONFIG["TEMPLATE_DIRS"]:
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

        for static_file in [CONFIG["README"], CONFIG["UPLOAD_SCROLL"]]:
            sf_path = Path(static_file)
            if sf_path.exists():
                zipf.write(sf_path, arcname=sf_path.name)

        if CONFIG["INCLUDE_REGISTRY"]:
            reg_path = Path(CONFIG["REGISTRY_FILE"])
            if reg_path.exists():
                zipf.write(reg_path, arcname=reg_path.name)

    # === Write Lockfile ===
    with open(lockfile_path, "w") as f:
        yaml.dump(lockfile, f, sort_keys=False)

    print(f"Package written to: {output_zip_path}")
    print(f"Lockfile written to: {lockfile_path}")


if __name__ == "__main__":
    main()
