from pathlib import Path
from typing import cast
import yaml
from .protocol_process import ProtocolProcess
from ....config.pkg_config import PkgConfig
from ...front_mater_meta import FrontMatterMeta
from ...main_registery import MainRegistry


class ProcessTemplateRegistry(ProtocolProcess):
    def __init__(self, worksapce_dir: Path | str, registry: MainRegistry):
        self._workspace_dir = Path(worksapce_dir)
        self._main_registry = registry
        self.config = PkgConfig()

    def get_dest_path(self, tokens: dict) -> Path:
        """
        Gets the Destination Path for the Manifest

        Args:
            tokens (dict): tokens, VER requied in tokens

        Returns:
            Path: Path of the file
        """
        if "VER" not in tokens:
            raise KeyError("VER not in Tokens")
        dest_path = (
            self._workspace_dir
            / f"{self.config.template_manifest_name}-{tokens['VER']}.yml"
        )
        return dest_path

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

    def _build_registry(self, kw: dict) -> dict:
        reg_dict = {
            "template_manifest_registry": {
                "bundle_version": str(kw["VER"]),
                "package_version": str(kw["VER"]),
                "batch_uid": f"{self.config.batch_prefix}-{kw['VER']}-{kw['BATCH_HASH']}",
                "batch_hash": kw["BATCH_HASH"],
                "declared_registry": self._main_registry.reg_id,
                "registry_version": self._main_registry.reg_version,
                "generated_at": kw["DATE"],
                "manifest_scope": "locked_only",
                "manifest_keyed_by": "template_id",
                "application_state": {
                    "applied_in_session": False,  # Automatically set to true once the manifest is parsed and trusted in the current thread
                    "mirrorwall_indexed": False,  # Set to true if any template in this manifest is embedded into the Mirrorwall
                    "applied_timestamp": None,  # Populated with UTC timestamp of first manifest activation, e.g. "2025-12-01T15:24:10Z"
                    "mirrorwall_first_embed": None,  # First template_id embedded from this bundle into the Mirrorwall (if any)
                    "embed_count": 0,  # Running total of templates from this manifest embedded into the Mirrorwall
                    "triggered_by": None,  # System user or agent that triggered first application (e.g., "Soluun", "Adamus", "Console-Ingest")
                },
                "template_count": 0,
                "template_ids": [],
                "templates": {},
            }
        }
        # reg_dict["codex_binding_contract"] = {
        #     "enforced": True,
        #     "version": "1.0",
        #     "notes": "This manifest-lockfile pair is bidirectionally bound. Identity resolution, hash enforcement, and registry alignment are strictly enforced. Placeholder inference and category expansion are forbidden unless declared explicitly.",
        # }
        self.config.codex_binding_contract.update_yaml_dict(reg_dict)
        self._build_templates(kw, reg_dict)
        lock_file_path = (
            self._workspace_dir
            / f"{self.config.lock_file_name}-{kw['VER']}{self.config.lock_file_ext}"
        )
        reg_dict["generated_from_lockfile"] = {
            "file_name": lock_file_path.name,
            "lockfile_uid": f"{self.config.batch_prefix}-{kw['VER']}-{kw['BATCH_HASH']}",
        }

        # generated_from_lockfile:
        #     file_name: codex-template-55.lock
        #     lockfile_uid: codex-batch-55-a1b2c3d4e5f6

        template_data = cast(dict[str, FrontMatterMeta], kw["TEMPLATES_DATA"])
        reg_dict["canonical_template_sha256_hash_map"] = {}
        reg_dict["canonical_template_id_to_template_type_map"] = {}
        reg_dict["canonical_template_type_to_template_id_map"] = {}
        reg_dict["canonical_template_id_file_name_map"] = {}
        for sha_str, fm in template_data.items():
            reg_dict["canonical_template_sha256_hash_map"][fm.template_id] = sha_str
            reg_dict["canonical_template_id_to_template_type_map"][fm.template_id] = (
                fm.template_type
            )
            reg_dict["canonical_template_type_to_template_id_map"][fm.template_type] = (
                fm.template_id
            )
            reg_dict["canonical_template_id_file_name_map"][fm.template_id] = (
                fm.file_path.name
            )

        return reg_dict

    def _build_templates(self, kw: dict, reg_dict: dict) -> None:
        tp = cast(dict[str, FrontMatterMeta], kw["TEMPLATES_DATA"])
        templates_section = reg_dict["template_manifest_registry"]["templates"]
        template_ids = reg_dict["template_manifest_registry"]["template_ids"]
        for sha_str, fm in tp.items():
            # fm = FrontMatterMeta(path)
            templates_section[fm.template_id] = {
                "template_name": fm.template_name,
                "template_id": fm.template_id,
                "template_version": fm.template_version,
                "template_category": fm.template_category,
                "template_type": fm.template_type,
                "file_name": fm.file_path.name,
                "sha256": sha_str,
            }
            reg_dict["template_manifest_registry"]["template_count"] += 1
            template_ids.append(fm.template_id)

    def process(self, tokens: dict) -> Path:
        """
        Process the README source file and return its content as a string.
        Args:
            tokens (dict): A dictionary of tokens to replace in the README.
        Returns:
            Path: The path to the processed README file.
        """
        self._validate_tokens(tokens)

        file_path = self.get_dest_path(tokens)

        manifest = self._build_registry(tokens)

        with open(file_path, "w") as manifest_f:
            yaml.dump(manifest, manifest_f, Dumper=yaml.Dumper, sort_keys=False)

        return file_path

    def get_process_name(self) -> str:
        """
        Gets the process name for this instance

        Returns:
            str: Process Name
        """
        return "ProcessTemplateRegistry"
