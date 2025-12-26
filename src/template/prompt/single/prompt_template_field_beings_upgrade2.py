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

    def _get_ced(self, fm: FrontMatterMeta, tokens: dict) -> str:
        return f"""## 🌀 Canonical Executor Declaration (CEIB-V{self.config.template_ceib_single.version})

{self._backticks_secondary}yaml
executor_mode: {self.config.template_ceib_single.executor_mode}-V{self.config.template_ceib_single.version}
template_file: {fm.file_path.name}
registry_file: {fm.template_type}-template-v{fm.template_version}-registry.yml
artifact_name: {{Artifact Name}}
tempalte_hash: {fm.sha256}
canonical_mode: true
template_strict_integrity: true`
disable_template_id_reference: true
disable_memory_templates: true
forbid_inference: true
placeholder_resolution: true
abort_on_field_mismatch: false
abort_on_placeholder_failure: true
render_section_order: from_template_body
render_only_declared_sections: true
validate_fields_from_registry: true
field_diff_mode: clean_and_report
include_field_diff_report: true
output_mode:
  - console
  - obsidian
  - mirrorwall
template_output_mode:
  include_executor_metadata: true
  include_placeholder_meta: true
{self._backticks_secondary}
"""

    def _get_invocation_ext(
        self, entry: TemplateEntry, fm: FrontMatterMeta, tokens: dict
    ) -> str:
        result = PromptTemplateFieldBeings2._get_invocation_ext(self, entry, fm, tokens)

        if self.config.templates_config_info.tci_items[fm.template_type].expected_image:
            result += "\nAttached is the the artifact image."
        result += (
            "\nThe application of this template is an upgrade for the markdown below."
        )
        return result

    def _get_prompt_suffix(self, fm: FrontMatterMeta, tokens: dict) -> str:
        return "\n\n```md\n{Markdown here}\n```"
