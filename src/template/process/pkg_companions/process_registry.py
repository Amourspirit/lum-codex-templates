from pathlib import Path
from typing import Any
import yaml
from .protocol_process import ProtocolProcess
from ....config.pkg_config import PkgConfig
from ...main_registery import MainRegistry
from ...front_mater_meta import FrontMatterMeta


class ProcessRegistry(ProtocolProcess):
    def __init__(self, workspace_dir: Path | str, registry: MainRegistry):
        self._workspace_dir = Path(workspace_dir)
        self._main_registry = registry
        self.config = PkgConfig()
        self.file_src = self.config.root_path / self.config.reg_file

    def _validate_tokens(self, kw: dict) -> None:
        required_tokens = set(["DATE", "TEMPLATES_DATA", "TEMPLATE_META"])
        for token in required_tokens:
            if token not in kw:
                raise ValueError(f"Missing required token: {token}")

    def get_dest_path(self, tokens: dict) -> Path:
        """
        Gets the Destination Path for the Manifest

        Args:
            tokens (dict): tokens, not currently used but here for future usage and consistency.

        Returns:
            Path: Path of the file
        """
        dest_path = self._workspace_dir / self.file_src.name
        return dest_path

    def _get_template_meta(self, tokens: dict) -> dict[str, dict]:
        """
        Extracts the TEMPLATE_META from the provided tokens.

        Args:
            tokens (dict): A dictionary of tokens.
        Returns:
            dict[str, dict]: The TEMPLATE_META dictionary.
        Raises:
            ValueError: If TEMPLATE_META is missing or not in the expected format.
        """
        if "TEMPLATE_META" not in tokens:
            raise ValueError("TEMPLATE_META token is missing.")
        template_meta = tokens["TEMPLATE_META"]
        if not isinstance(template_meta, dict):
            raise ValueError("TEMPLATE_META token is not a dictionary.")
        return template_meta

    def _get_template_data(self, tokens: dict) -> dict[str, FrontMatterMeta]:
        """
        Extracts the TEMPLATES_DATA from the provided tokens.

        Args:
            tokens (dict): A dictionary of tokens.
        Returns:
            dict: The TEMPLATES_DATA dictionary (dict[str, FrontMatterMeta]).
        Raises:
            ValueError: If TEMPLATES_DATA is missing or not in the expected format.
        """
        if "TEMPLATES_DATA" not in tokens:
            raise ValueError("TEMPLATES_DATA token is missing.")
        templates_data = tokens["TEMPLATES_DATA"]
        if not isinstance(templates_data, dict):
            raise ValueError("TEMPLATES_DATA token is not a dictionary.")
        return templates_data

    def _get_template_families(self, tokens: dict) -> dict[str, Any]:
        """
        Builds a mapping from template families to their member template IDs.
        Args:
            tokens (dict): A dictionary of tokens.
        Returns:
            dict: A mapping (dict[str, Any]) from template families to their member template IDs.
        """
        template_data = self._get_template_data(tokens)
        template_families: dict[str, Any] = {}
        for template_type, fm in template_data.items():
            if fm.template_family not in template_families:
                template_families[fm.template_family] = {}
            if "members" not in template_families[fm.template_family]:
                template_families[fm.template_family]["members"] = []
            template_families[fm.template_family]["members"].append(fm.template_id)

        return template_families

    def _get_template_front_matter_meta(
        self, template_type: str, template_meta: dict
    ) -> FrontMatterMeta:
        """
        Retrieves the front matter metadata for a specific template type.

        Args:
            template_type (str): The template type to look up.
            template_meta (dict): The TEMPLATE_META dictionary.
        Returns:
            dict: The front matter metadata for the specified template type.
        Raises:
            ValueError: If the front matter metadata is missing for the specified template type.
        """
        # template_meta = self._get_template_meta(tokens)
        if template_type not in template_meta:
            raise ValueError(
                f"Template type '{template_type}' not found in TEMPLATE_META."
            )
        fm_meta = template_meta[template_type].get("template_front_matter_meta")
        if fm_meta is None:
            raise ValueError(
                f"Front matter meta missing for template type '{template_type}'."
            )
        return fm_meta

    def _get_template_id_to_template_type_map(self, tokens: dict) -> dict[str, str]:
        """
        Builds a mapping from template IDs to template types.

        Args:
            tokens (dict): A dictionary of tokens.
        Returns:
            dict[str, str]: A mapping from template IDs to template types.
        Raises:
            ValueError: If any template type is missing a template ID.
        """
        template_meta = self._get_template_meta(tokens)
        template_id_map: dict[str, str] = {}
        for template_type, meta in template_meta.items():
            fm = self._get_template_front_matter_meta(template_type, template_meta)
            template_id_map[fm.template_id] = fm.template_type
        return template_id_map

    def _get_template_type_to_template_id_map(self, tokens: dict) -> dict[str, str]:
        """
        Builds a mapping from template types to template IDs.

        Args:
            tokens (dict): A dictionary of tokens.
        Returns:
            dict[str, str]: A mapping from template types to template IDs.
        Raises:
            ValueError: If any template type is missing a template ID.
        """
        template_meta = self._get_template_meta(tokens)
        template_type_map: dict[str, str] = {}
        for template_type, meta in template_meta.items():
            fm = self._get_template_front_matter_meta(template_type, template_meta)
            template_type_map[fm.template_type] = fm.template_id
        return template_type_map

    def _get_template_field_matrix(self, tokens: dict) -> dict[str, dict]:
        """
        Builds a mapping from template types to their field matrices.

        Args:
            tokens (dict): A dictionary of tokens.
        Returns:
            dict[str, dict]: A mapping from template types to their field matrices.
        Raises:
            ValueError: If any template type is missing a field matrix.
        """
        template_meta = self._get_template_meta(tokens)
        template_field_matrix: dict[str, dict] = {}
        for template_type, meta in template_meta.items():
            fm = self._get_template_front_matter_meta(template_type, template_meta)
            template_field_matrix[template_type] = {
                "template_id": fm.template_id,
                "file_name": fm.file_path.name,
                self.config.template_hash_field_name: fm.sha256,
            }
            for key, value in meta.items():
                if key not in self.config.template_meta_keys:
                    continue
                template_field_matrix[template_type][key] = value
        return template_field_matrix

    def _get_template_types(self, tokens: dict) -> list[str]:
        """
        Extracts the list of template types from the provided tokens.
        """
        template_meta = self._get_template_meta(tokens)
        return sorted(list(template_meta.keys()))

    def _set_template_hash_enforcement(self, tokens: dict, mmr: dict) -> None:
        """
        Builds a mapping from template types to their hash enforcement status.

        Args:
            tokens (dict): A dictionary of tokens.
        Returns:
            None:
        """
        mmr["template_hash_enforcement"] = {
            "field_name": self.config.template_hash_field_name,
            "algorithm": "sha256",
            "hash_scope": {
                "include": ["yaml_frontmatter", "template_body"],
                "exclude_fields": [self.config.template_hash_field_name],
            },
            "canonicalize_before_hashing": True,
            "enforce_in_all_templates": True,
        }

    def process(self, tokens: dict) -> Path:
        """
        Process the Registry source file and return its content as a string.
        Args:
            tokens (dict): A dictionary of tokens to replace in the README.
        Returns:
            Path: The path to the processed README file.
        """
        if not self.file_src.exists():
            raise FileNotFoundError(f"README source file not found: {self.file_src}")
        self._validate_tokens(tokens)
        file_path = self._workspace_dir / self.file_src.name
        # copy source to destination
        with self.file_src.open("r", encoding="utf-8") as f_src:
            mmr = yaml.safe_load(f_src)
        template_id_map = self._get_template_id_to_template_type_map(tokens)
        # Update the registry entries with template types
        mmr["template_id_to_template_type_map"] = template_id_map
        template_type_map = self._get_template_type_to_template_id_map(tokens)
        mmr["template_type_to_template_id_map"] = template_type_map
        mmr["entry_date"] = tokens["DATE"]

        template_field_matrix = self._get_template_field_matrix(tokens)
        mmr["template_field_matrix_by_template_type"] = template_field_matrix
        self._set_template_hash_enforcement(tokens, mmr)
        mmr["version"] = self._main_registry.reg_version
        mmr["valid_template_types"] = self._get_template_types(tokens)

        mmr["template_field_registry_matrix"] = {
            "source": f"{self.config.lock_file_name}-{tokens['VER']}{self.config.lock_file_ext}",
            "path": "templates → template_id → fields",
            "enforcement_mode": "strict",
            "validate_against": ["template_fields_declared", "metadata_fields"],
        }
        template_families = self._get_template_families(tokens)
        mmr["template_families"] = template_families

        with file_path.open("w", encoding="utf-8") as f_dest:
            yaml.safe_dump(mmr, f_dest, sort_keys=False)
        return file_path

    def get_process_name(self) -> str:
        """
        Gets the process name for this instance

        Returns:
            str: Process Name
        """
        return "ProcessRegistry"
