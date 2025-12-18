from typing import cast
from pathlib import Path
import yaml
from .protocol_support import ProtocolSupport
from ....config.pkg_config import PkgConfig
from ...main_registry import MainRegistry
from ...front_mater_meta import FrontMatterMeta
from .prompt_template_field_beings import PromptTemplateFieldBeings
from .meta_helpers.prompt_meta_type import PromptMetaType, TemplateEntry


class PromptTemplateFieldBeingsUpgrade(PromptTemplateFieldBeings, ProtocolSupport):
    def __init__(self, registry: MainRegistry) -> None:
        super().__init__(registry)
        self._backticks = "~~~"

    def _get_output_path(self, tokens: dict) -> Path:
        return (
            self._dest_dir
            / f"{self.config.template_to_field_being_upgrade_map_name}-{tokens['VER']}.md"
        )

    def _get_invocation_ext(
        self, entry: TemplateEntry, fm: FrontMatterMeta, tokens: dict
    ) -> str:
        return f"""{entry.invocation},
to render the following template in **full canonical markdown**, including all required metadata **and** `template_body`,  
for **{{Artifact Name}}**, applying strict Codex enforcement.
Attached is the the artifact image.
The application of this template is an upgrade for the markdown below."""

    def _get_prompt_suffix(self, fm: FrontMatterMeta, tokens: dict) -> str:
        return "\n\n```md\n{Markdown here}\n```"
