from pathlib import Path
from typing import cast
import yaml
from .protocol_process import ProtocolProcess
from ....config.pkg_config import PkgConfig
from ...front_mater_meta import FrontMatterMeta
from ...main_registery import MainRegistry


class ProcessLock(ProtocolProcess):
    def __init__(self, worksapce_dir: Path | str, registry: MainRegistry):
        self._workspace_dir = Path(worksapce_dir)
        self._main_registry = registry
        self.config = PkgConfig()
        self.file_src = self.config.root_path / self.config.readme_src

    def _validate_tokens(self, kw: dict) -> None:
        required_tokens = set(
            [
                "DATE",
                "VER",
                "BATCH_HASH",
                "BUILDER_VER",
                "TEMPLATE_COUNT",
                "TEMPLATE_PATHS",
                "SHA256",
            ]
        )
        for token in required_tokens:
            if token not in kw:
                raise ValueError(f"Missing required token: {token}")

    def _build_lockfile(self, kw: dict) -> dict:
        lockfile = {
            "package_version": str(kw["VER"]),
            "batch_uid": f"{self.config.batch_prefix}-{kw['VER']}-{kw['BATCH_HASH']}",
            "batch_hash": kw["BATCH_HASH"],
            "lockfile_version": str(kw["VER"]),
            "registry_version": self._main_registry.reg_version,
            "builder_version": self.config.version,
            "generated_at": kw["DATE"],
            "strict_field_mode": self.config.strict_field_mode,
            "force_invalidate_previous": self.config.force_invalidate_previous,
            "auto_invoke_protocol_scroll": f"{self.config.auto_invoke_scroll}-{kw['VER']}.md",
            "strict_hash_mode": self.config.strict_hash_mode,
            "registry_sources": {
                "registry_id": self._main_registry.reg_id,
                "name": self._main_registry.reg_name,
                "path": self._main_registry.file_name,
                "version": self._main_registry.reg_version,
                "format": "yaml",
                "enforced": True,
                "sha256": kw["SHA256"],
            },
            "categories": [],
        }
        return lockfile

    def _build_lockfile_categories(
        self, file_path: Path, fm: FrontMatterMeta, categories_map: dict, kw: dict
    ) -> None:
        template_meta = {
            "template_name": fm.template_name,
            "template_id": fm.template_id,
            "template_category": fm.template_category,
            "template_type": fm.template_type,
            "template_version": fm.template_version,
            "path": f"./{file_path.name}",
            "sha256": kw["SHA256"],
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

    def _process_template_paths(self, categories_map: dict, kw: dict):
        paths = cast(list[Path], kw["TEMPLATE_PATHS"])
        for file_path in paths:
            if not file_path.exists():
                raise FileNotFoundError(f"Template file not found: {file_path}")
            fm = FrontMatterMeta(file_path)
            if not fm.has_field("template_id"):
                raise ValueError(f"Template missing 'template_id': {file_path}")

            self._build_lockfile_categories(file_path, fm, categories_map, kw)

    def process(self, tokens: dict) -> Path:
        """
        Process the README source file and return its content as a string.
        Args:
            tokens (dict): A dictionary of tokens to replace in the README.
        Returns:
            Path: The path to the processed README file.
        """
        if not self.file_src.exists():
            raise FileNotFoundError(f"README source file not found: {self.file_src}")

        self._validate_tokens(tokens)

        file_path = (
            self._workspace_dir
            / f"{self.config.lock_file_name}-{tokens['VER']}{self.config.lock_file_ext}"
        )
        categories_map = {}
        lockfile = self._build_lockfile(tokens)
        self._process_template_paths(categories_map, tokens)

        # Convert map back to list for lockfile
        lockfile["categories"] = list(categories_map.values())

        with open(file_path, "w") as lockfile_f:
            yaml.dump(lockfile, lockfile_f, Dumper=yaml.Dumper, sort_keys=False)

        return file_path

    def get_process_name(self) -> str:
        """
        Gets the process name for this instance

        Returns:
            str: Process Name
        """
        return "ProcessLock"
