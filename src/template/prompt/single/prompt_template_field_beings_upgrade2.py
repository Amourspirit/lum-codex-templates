from pathlib import Path
from typing import Any
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

    def _get_ced(
        self, entry: TemplateEntry, fm: FrontMatterMeta, tokens: dict
    ) -> dict[str, Any]:
        # return f"""## 🌀 Canonical Executor Declaration (CEIB-V{self.config.template_ceib_single.version})
        result = PromptTemplateFieldBeings2._get_ced(self, entry, fm, tokens)
        if "artifact_name" in result["data"]:
            del result["data"]["artifact_name"]
        result["data"] = self._insert_at(result["data"], "template_hash", fm.sha256, 2)
        result["data"]["template_output_mode"] = {
            "include_executor_metadata": True,
            "include_placeholder_meta": True,
            "outputs": ["file", "console", "mirrorwall", "obsidian", "web_preview"],
            "format": "markdown",
        }
        return result

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
