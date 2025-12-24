from pathlib import Path
from ..protocol_support import ProtocolSupport
from ...main_registry import MainRegistry
from ...front_mater_meta import FrontMatterMeta
from .prompt_template_field_beings2 import PromptTemplateFieldBeings2
from ..meta_helpers.prompt_meta_type import TemplateEntry


class PromptTemplateFieldBeingsUpgrade2(PromptTemplateFieldBeings2, ProtocolSupport):
    def __init__(self, registry: MainRegistry) -> None:
        super().__init__(registry)

    def _get_output_path(self, tokens: dict) -> Path:
        return (
            self._dest_dir
            / f"single-{self.config.template_to_field_being_upgrade_map_name}2-{tokens['VER']}.md"
        )

    def _get_invocation_mode(self) -> str:
        return "upgrade"

    def _get_invocation_ext(
        self, entry: TemplateEntry, fm: FrontMatterMeta, tokens: dict
    ) -> str:
        result = f"""I invoke **{self.config.template_ceib_single.executor_mode}-V{self.config.template_ceib_single.version}**
of file `{self.config.template_ceib_single.executor_mode}-V{self.config.template_ceib_single.version}.md`  
and {entry.invocation} to apply `{fm.template_type}-v{fm.template_version}.md`  
with registry `{fm.template_type}-v{fm.template_version}-registry.yml`  
for artifact **{{Artifact Name}}**.
"""
        if self.config.templates_config_info.tci_items[fm.template_type].expected_image:
            result += "\nAttached is the the artifact image."
        result += (
            "\nThe application of this template is an upgrade for the markdown below."
        )
        return result

    def _get_prompt_suffix(self, fm: FrontMatterMeta, tokens: dict) -> str:
        return "\n\n```md\n{Markdown here}\n```"
