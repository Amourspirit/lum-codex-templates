from pathlib import Path
from typing import cast
import yaml
from .protocol_process import ProtocolProcess
from .process_registry import ProcessRegistry
from .process_template_registry import ProcessTemplateRegistry
from ....config.pkg_config import PkgConfig
from ...front_mater_meta import FrontMatterMeta
from ...main_registery import MainRegistry
from ....util import sha


class ProcessLock(ProtocolProcess):
    def __init__(self, worksapce_dir: Path | str, registry: MainRegistry):
        self._workspace_dir = Path(worksapce_dir)
        self._main_registry = registry
        self.config = PkgConfig()

    def _validate_tokens(self, kw: dict) -> None:
        required_tokens = set(
            [
                "DATE",
                "VER",
                "BATCH_HASH",
                "BUILDER_VER",
                "TEMPLATE_COUNT",
                "TEMPLATES_DATA",
            ]
        )
        for token in required_tokens:
            if token not in kw:
                raise ValueError(f"Missing required token: {token}")

    def _build_lockfile(self, kw: dict) -> dict:
        lockfile = {
            "package_version": str(kw["VER"]),
            "templates_keyed_by": "template_id",
            "registry_version": self._main_registry.reg_version,
            "batch_uid": f"{self.config.batch_prefix}-{kw['VER']}-{kw['BATCH_HASH']}",
            "batch_hash": kw["BATCH_HASH"],
            "lockfile_version": str(kw["VER"]),
            "builder_version": self.config.version,
            "generated_at": kw["DATE"],
            "strict_field_mode": self.config.strict_field_mode,
            "force_invalidate_previous": self.config.force_invalidate_previous,
            "auto_invoke_protocol_scroll": f"{self.config.auto_invoke_scroll}-{kw['VER']}.md",
            "strict_hash_mode": self.config.strict_hash_mode,
            "enforce_strict_bundle_boundary": True,
            "template_version_scope": "locked_only",
            "template_index_scope": "flat",
            "template_count": 0,
            "manifest_sha256": None,
            "registry_sources": {
                "registry_id": self._main_registry.reg_id,
                "name": self._main_registry.reg_name,
                "path": self._main_registry.file_name,
                "version": self._main_registry.reg_version,
                "format": "yaml",
                "enforced": True,
                "sha256": None,
            },
        }

        self._update_manifest_sha(tokens=kw, lockfile=lockfile)
        self._update_registry_sha(tokens=kw, lockfile=lockfile)

        self.config.template_config.update_yaml_dict(lockfile)
        lockfile["template_ids"] = []
        # lockfile["codex_binding_contract"] = {
        #     "enforced": True,
        #     "version": "1.0",
        #     "notes": "This manifest-lockfile pair is bidirectionally bound. Identity resolution, hash enforcement, and registry alignment are strictly enforced. Placeholder inference and category expansion are forbidden unless declared explicitly.",
        # }
        self.config.codex_binding_contract.update_yaml_dict(lockfile)
        lockfile["templates"] = {}
        return lockfile

    def _update_registry_sha(self, tokens: dict, lockfile: dict) -> None:
        reg = ProcessRegistry(self._workspace_dir, self._main_registry)
        reg_path = reg.get_dest_path(tokens=tokens)
        if reg_path.exists():
            lockfile["registry_sources"]["sha256"] = sha.compute_sha256(reg_path)
        else:
            del lockfile[["registry_sources"]]["sha256"]
            print(
                f"Unable to calculate sha256 for registry file. File {reg_path.name} not found!"
            )

    def _update_manifest_sha(self, tokens: dict, lockfile: dict) -> None:
        reg = ProcessTemplateRegistry(self._workspace_dir, self._main_registry)
        manifest_path = reg.get_dest_path(tokens=tokens)
        if manifest_path.exists():
            lockfile["manifest_sha256"] = sha.compute_sha256(manifest_path)
        else:
            del lockfile["manifest_sha256"]
            print(
                f"Unable to calculate sha256 for manifest. File {manifest_path.name} not found!"
            )

    def _get_template_fields(self, fm: FrontMatterMeta) -> list[str]:
        fields = fm.get_keys()
        result_fields: list[str] = []
        field_map = self._main_registry.registry["metadata_fields"]

        for field in fields:
            if field not in field_map:
                continue
            field_info = field_map[field]
            # Skip deprecated fields
            # can alos be inactive but we only care about deprecated here
            if "status" in field_info and field_info["status"] == "deprecated":
                continue
            result_fields.append(field)
        return result_fields

    def _build_lockfile_templates(
        self, file_path: Path, fm: FrontMatterMeta, lockfile: dict, sha: str
    ) -> None:
        template_meta = {
            "template_name": fm.template_name,
            "template_id": fm.template_id,
            "template_category": fm.template_category,
            "template_type": fm.template_type,
            "template_version": fm.template_version,
            "path": file_path.name,
            "sha256": sha,
            "fields": self._get_template_fields(fm),
        }
        lockfile["template_count"] += 1
        lockfile["template_ids"].append(fm.template_id)
        lockfile["templates"][fm.template_id] = template_meta

    def _process_templates_data(self, lockfile: dict, kw: dict):
        template_data = cast(dict[str, FrontMatterMeta], kw["TEMPLATES_DATA"])
        for sha_str, fm in template_data.items():
            if not fm.file_path.exists():
                raise FileNotFoundError(f"Template file not found: {fm}")
            # fm = FrontMatterMeta(file_path)
            if not fm.has_field("template_id"):
                raise ValueError(f"Template missing 'template_id': {fm}")

            self._build_lockfile_templates(fm.file_path, fm, lockfile, sha_str)

    def process(self, tokens: dict) -> Path:
        """
        Process the README source file and return its content as a string.
        Args:
            tokens (dict): A dictionary of tokens to replace in the README.
        Returns:
            Path: The path to the processed README file.
        """

        self._validate_tokens(tokens)

        file_path = (
            self._workspace_dir
            / f"{self.config.lock_file_name}-{tokens['VER']}{self.config.lock_file_ext}"
        )
        lockfile = self._build_lockfile(tokens)
        self._process_templates_data(lockfile, tokens)

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
