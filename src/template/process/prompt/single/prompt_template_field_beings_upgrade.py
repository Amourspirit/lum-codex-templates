from pathlib import Path
from ..protocol_support import ProtocolSupport
from ....main_registry import MainRegistry
from ....front_mater_meta import FrontMatterMeta
from .prompt_template_field_beings import PromptTemplateFieldBeings
from ..meta_helpers.prompt_meta_type import TemplateEntry


class PromptTemplateFieldBeingsUpgrade(PromptTemplateFieldBeings, ProtocolSupport):
    def __init__(self, registry: MainRegistry) -> None:
        super().__init__(registry)

    def _get_output_path(self, tokens: dict) -> Path:
        return (
            self._dest_dir
            / f"single-{self.config.template_to_field_being_upgrade_map_name}-{tokens['VER']}.md"
        )

    def _get_invocation_mode(self) -> str:
        return "upgrade"

    def _get_invocation_ext(
        self, entry: TemplateEntry, fm: FrontMatterMeta, tokens: dict
    ) -> str:
        result = f"""{entry.invocation},
to render the following template in **full canonical markdown**, including all required metadata **and** `template_body`,  
for **{{Artifact Name}}**, applying strict Codex enforcement.
"""
        if self.config.templates_config_info.tci_items[fm.template_type].expected_image:
            result += "\nAttached is the the artifact image."
        result += (
            "\nThe application of this template is an upgrade for the markdown below."
        )
        return result

    def _get_prompt_suffix(self, fm: FrontMatterMeta, tokens: dict) -> str:
        return "\n\n```md\n{Markdown here}\n```"
