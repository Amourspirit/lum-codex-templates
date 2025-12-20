from typing import Any
from pathlib import Path
from ....main_registry import MainRegistry
from ....front_mater_meta import FrontMatterMeta
from .....config.pkg_config import PkgConfig
from .template_base import TemplateBase
from .protocol_template_reg import ProtocolTemplateReg


class TemplateLinkageScroll(TemplateBase, ProtocolTemplateReg):
    def __init__(
        self,
        working_dir: Path,
        main_registry: MainRegistry,
        templates_meta: dict[str, dict[str, Any]],
        templates_data: dict[str, FrontMatterMeta],
    ):
        config = PkgConfig()
        type_name = config.templates_config_info.tci_items[
            "linkage_scroll"
        ].template_type
        template_data = templates_data.get(type_name)
        if template_data is None:
            raise ValueError(f"Template data for type '{type_name}' not found.")
        super().__init__(working_dir, main_registry, templates_meta, template_data)

    def _validate_tokens(self, tokens: dict[str, Any]) -> None:
        # Placeholder for token validation logic
        pass

    def process(self, tokens: dict[str, Any]) -> tuple[str, Path]:
        """
        Validate input tokens, convert them into a registry dictionary, and persist the result as a YAML file.

        Args:
            tokens (dict[str, Any]): Token mapping used to build the registry payload. Must satisfy the validator used by
                self._validate_tokens.

        Returns:
            tuple[str, Path]: A tuple of (template_type, path) where template_type is taken from self.fm.template_type
            and path is the filesystem Path to the written YAML file.

        Raises:
            Any exception raised by the underlying helpers (e.g., self._validate_tokens, self._process_common,
            self._write_yaml_file) will propagate to the caller.

        Side effects:
            Writes a YAML file to disk via self._write_yaml_file.
        """

        self._validate_tokens(tokens)
        reg_dict = self._process_common(tokens)
        p = self._write_yaml_file(reg_dict)
        return self.fm.template_type, p
