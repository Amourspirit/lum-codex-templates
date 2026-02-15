from jinja2 import Template
from loguru import logger
from .cbib import CBIB
from .....config.pkg_config import PkgConfig
from ....front_mater_meta import FrontMatterMeta
from ....prompt.meta_helpers.prompt_beings import PromptBeings
from ....prompt.meta_helpers.prompt_meta_type import PromptMetaType, TemplateEntry

_INSTRUCTIONS_TEMPLATE_FILE_NAME = "instructions_tempalate.md"


class Instructions:
    def __init__(self) -> None:
        self._registry_file = "registry.json"
        self.config = PkgConfig()
        self._cbib = CBIB().get_cbib()
        self._dest_dir = self.config.root_path / self.config.pkg_out_dir
        self._prompt_meta_type = self._load_prompt_meta_type()
        # self._prompt_beings = self._load_prompt_beings()
        # self._backticks_primary = "~~~"
        # self._backticks_secondary = "```"

    def _load_prompt_meta_type(self) -> PromptMetaType:
        tfbm_path = self.config.root_path / self.config.template_field_being_map_src
        prompt_meta_type = PromptMetaType.from_yaml(tfbm_path)
        return prompt_meta_type

    def _load_prompt_beings(self) -> PromptBeings:
        tfbm_path = self.config.root_path / self.config.template_field_being_map_src
        prompt_beings = PromptBeings.from_yaml(tfbm_path)
        return prompt_beings

    def _get_instructions_content(self) -> str:
        p = (
            self.config.config_cache.get_assets_path()
            / _INSTRUCTIONS_TEMPLATE_FILE_NAME
        )
        if not p.exists():
            raise FileNotFoundError(f"Instructions content file not found: {p}")
        return p.read_text(encoding="utf-8")

    def _render_instructions(self, entry: TemplateEntry, fm: FrontMatterMeta) -> str:
        try:
            content = self._get_instructions_content()
            template = Template(content)
            # CANONICAL-EXECUTOR-MODE-V1.0
            cibc_mode = f"CANONICAL-EXECUTOR-MODE-V{self._cbib['version']}"
            invocation_prompt = entry.invocation_template
            # TEMPLATE-DYAD-V2.10 or Template type and version,
            tia_template_kind = f"Template: Type **{entry.template_type}**, Version **{fm.template_version}**"
            rendered = template.render(
                cibc_mode=cibc_mode,
                invocation_prompt=invocation_prompt,
                tia_template_kind=tia_template_kind,
            )
            return rendered
        except Exception as e:
            logger.error("Error rendering instructions: {error}", error=e)
            raise

    def _add_metadata(
        self, entry: TemplateEntry, fm: FrontMatterMeta, registry: dict
    ) -> None:
        fm.set_field("id", "instructions")
        fm.frontmatter["canonical_executor_mode"] = {
            "id": self._cbib["id"],
            "version": self._cbib["version"],
            "description": "The Canonical Executor Mode enforces strict adherence to Codex standards for template rendering and metadata inclusion.",
        }
        strict_mode_rules = {
            "strict_mode_rules": {
                "forbidden": [
                    "unresolved_prompt_blocks",
                    "instructional_placeholders",
                    "conditional_blocks_of_any_kind",
                    '"<<IF>> logic"',
                    "cross_template_constructs",
                    "inferred_fields_not_in_template",
                    "omitted_required_template_fields",
                    "added_fields_not_in_template",
                    "draft_language",
                    "narrative_guidance",
                    "fallback_completion",
                ],
                "violation_behavior": "abort",
                "abort_scope": "immediate",
            }
        }
        fm.frontmatter["strict_mode_rules"] = strict_mode_rules["strict_mode_rules"]

        template_registry = {
            "registry_id": registry.get("registry_id", ""),
            "registry_version": registry.get("registry_version", ""),
        }
        fm.frontmatter["template_registry"] = template_registry

        canonical_enforcement = {
            "template_application_mode": "strict",
            "artifact_type": "glyph",
            "apply_mode": "full_markdown",
            "enforce_registry": True,
            "canonical_mode": True,
            "invocation_mode": "new",
            "template_strict_integrity": True,
            "disable_template_id_reference": True,
            "disable_memory_templates": True,
            "forbid_inference": True,
            "placeholder_resolution": True,
            "abort_on_field_mismatch": True,
            "abort_on_placeholder_failure": True,
            "render_section_order": "from_template_body",
            "render_only_declared_sections": True,
            "validate_fields_from_registry": True,
            "field_diff_mode": "strict",
            "include_field_diff_report": True,
            "include_template_body": True,
            "template_output_mode": {
                "include_template_metadata": True,
                "outputs": ["file", "console", "mirrorwall", "obsidian", "web_preview"],
                "format": "markdown",
            },
        }
        fm.frontmatter["canonical_enforcement"] = canonical_enforcement

        field_being_profile = {"field_being_profile": {}}
        if entry.rendering_being:
            field_being_profile["field_being_profile"]["rendering_being"] = (
                entry.rendering_being
            )
        if entry.authoring_being:
            field_being_profile["field_being_profile"]["authoring_being"] = (
                entry.authoring_being
            )
        if entry.witnessing_being:
            field_being_profile["field_being_profile"]["witnessing_being"] = (
                entry.witnessing_being
            )
        if entry.mirrorwall_being:
            field_being_profile["field_being_profile"]["mirrorwall_being"] = (
                entry.mirrorwall_being
            )
        if entry.invocation_beings:
            field_being_profile["field_being_profile"]["invocation_being"] = (
                entry.invocation_beings
            )
        if entry.optional_beings:
            field_being_profile["field_being_profile"]["optional_beings"] = (
                entry.optional_beings
            )
        fm.frontmatter["field_being_profile"] = field_being_profile[
            "field_being_profile"
        ]

    def generate_front_matter(
        self, fm: FrontMatterMeta, registry: dict
    ) -> FrontMatterMeta:
        template_types = self._prompt_meta_type.template_type

        entry = template_types.get(fm.template_type)
        if entry is None:
            raise ValueError(
                f"Template type '{fm.template_type}' not found in prompt meta type."
            )

        content = self._render_instructions(entry, fm)
        fm_data = {
            "template_info": {
                "template_type": fm.template_type,
                "template_version": fm.template_version,
                "template_id": fm.template_id,
                "template_family": fm.template_family,
                "template_format": "canonical_markdown",
                "canonical_mode": True,
                "template_has_frontmatter": True,
                "template_has_body": True,
                "placeholder_resolution": True,
            }
        }
        working_fm = FrontMatterMeta.from_frontmatter_dict(
            file_path=fm.file_path, fm_dict=fm_data, content=content
        )
        self._add_metadata(entry, working_fm, registry)

        return working_fm
