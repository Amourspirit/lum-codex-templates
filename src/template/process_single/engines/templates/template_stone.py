from typing import Any
from pathlib import Path
from ....main_registry import MainRegistry
from .....config.pkg_config import PkgConfig
from ....front_mater_meta import FrontMatterMeta
from .template_base import TemplateBase
from .protocol_template import ProtocolTemplate


class TemplateStone(TemplateBase, ProtocolTemplate):
    def __init__(
        self,
        working_dir: Path,
        main_registry: MainRegistry,
        templates_data: dict[str, FrontMatterMeta],
    ):
        config = PkgConfig()
        type_name = config.templates_config_info.tci_items["stone"].template_type
        template_data = templates_data.get(type_name)
        if template_data is None:
            raise ValueError(f"Template data for type '{type_name}' not found.")
        super().__init__(working_dir, main_registry, template_data)

    def _validate_tokens(self, tokens: dict[str, Any]) -> None:
        # Placeholder for token validation logic
        pass

    def process(self, tokens: dict[str, Any]) -> FrontMatterMeta:
        self._validate_tokens(tokens)
        self._process_common(tokens)
        self.fm.recompute_sha256()
        p = self._write_file()
        return self.fm
