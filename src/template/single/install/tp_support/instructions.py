from dataclasses import field
from typing import Any
import yaml
from .cbib import CBIB
from .....config.pkg_config import PkgConfig
from ....front_mater_meta import FrontMatterMeta
from ....prompt.meta_helpers.prompt_beings import PromptBeings
from ....prompt.meta_helpers.prompt_meta_type import PromptMetaType, TemplateEntry


class Instructions:
    def __init__(self) -> None:
        self._registry_file = "registry.json"
        self.config = PkgConfig()
        self._cbib = CBIB().get_cbib()
        self._dest_dir = self.config.root_path / self.config.pkg_out_dir
        self._prompt_meta_type = self._load_prompt_meta_type()
        self._prompt_beings = self._load_prompt_beings()
        self._backticks_primary = "~~~"
        self._backticks_secondary = "```"

    def _load_prompt_meta_type(self) -> PromptMetaType:
        tfbm_path = self.config.root_path / self.config.template_field_being_map_src
        prompt_meta_type = PromptMetaType.from_yaml(tfbm_path)
        return prompt_meta_type

    def _load_prompt_beings(self) -> PromptBeings:
        tfbm_path = self.config.root_path / self.config.template_field_being_map_src
        prompt_beings = PromptBeings.from_yaml(tfbm_path)
        return prompt_beings

    def _get_invocation_agents(self, entry: TemplateEntry, registry: dict) -> str:
        agents = []
        for role, name in entry.invocation_agents.items():
            role_name = role.replace("_", " ").capitalize()
            if name.lower() == "current_user":
                new_name = self.config.env_user
            else:
                new_name = name
            agents.append(f"- {role_name}: {new_name}  ")
        return "\n".join(agents)

    def _get_field_binding_agents(self, entry: TemplateEntry) -> str:
        agents = []
        for role, name in entry.invocation_agents.items():
            role_name = role.lower()
            if name.lower() == "current_user":
                new_name = self.config.env_user
            else:
                new_name = name
            agents.append(f"  {role_name}: {new_name}")
        return "\n".join(agents)

    def _get_invocation_mode(self) -> str:
        return "new"

    def _get_invocation_ext(
        self, entry: TemplateEntry, fm: FrontMatterMeta, registry: dict
    ) -> str:
        return f"""{entry.invocation},
to render the following template in **full canonical markdown**, including all required metadata **and** `template_body`,  
for **{{Artifact Name}}**, applying strict Codex enforcement."""

    def _get_prompt_suffix(self, fm: FrontMatterMeta, registry: dict) -> str:
        return ""

    def _get_ced(self, fm: FrontMatterMeta, registry: dict) -> dict[str, Any]:
        # return f"""## 🌀 Canonical Executor Declaration (CEIB-V{self.config.template_ceib_single.version})
        registry_id = registry.get("registry_id")
        if not registry_id:
            raise ValueError("Registry ID not found in registry data.")
        registry_version = registry.get("registry_version")
        if not registry_version:
            raise ValueError("Registry version not found in registry data.")
        result: dict[str, Any] = {"title": "### ▸ Canonical Enforcement"}
        result["data"] = {
            # "executor_mode": f"{self.config.template_ceib_single.executor_mode}-V{self.config.template_ceib_single.version}",
            "template_file": f"{fm.file_path.name}",
            "registry_id": registry_id,
            "registry_file": self._registry_file,
            "template_version": fm.template_version,
            "registry_version": registry_version,
            "template_application_mode": "strict",
            "artifact_type": fm.template_category,
            "apply_mode": "full_markdown",
            "enforce_registry": True,
            "artifact_name": "{Artifact Name}",
            "canonical_mode": True,
            "invocation_mode": self._get_invocation_mode(),
            "template_type": fm.template_type,
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
        return result

    def _add_metadata(self, fm: FrontMatterMeta, registry: dict) -> None:
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

    def _gen_prompt(
        self, entry: TemplateEntry, fm: FrontMatterMeta, registry: dict
    ) -> str:
        registry_id = registry.get("registry_id")
        if not registry_id:
            raise ValueError("Registry ID not found in registry data.")
        registry_version = registry.get("registry_version")
        if not registry_version:
            raise ValueError("Registry version not found in registry data.")

        invocation_ext = self._get_invocation_ext(entry, fm, registry)
        prompt_suffix = self._get_prompt_suffix(fm, registry)
        invocation_agents = self._get_invocation_agents(entry, registry)
        # field_binding_agents = self._get_field_binding_agents(entry)
        # invocation_mode = self._get_invocation_mode()
        cde = self._get_ced(fm, registry)
        cid_title = cde["title"]
        cid_data = cde["data"]
        # convert cid_data to yaml block
        cid_yaml = yaml.dump(cid_data, sort_keys=False)

        prompt = f"""# 🌀 Template Application Instructions — {fm.template_id}

Use this declaration block to manually apply the template with full canonical enforcement.

* * *

## 🧼 Pre-Render Preparation

- Purge all prior template memory, cache entries, and inferred field maps.  
- Enforce this artifact as the **singular source of truth** under strict registry compliance.

* * *

## 🔐 Canonical Executor Reference

This template adheres to executor mode:

> **{self._cbib["id"]}**

📘 API Definition:  
[`[[API_RELATIVE_URL]]/executor_modes/CANONICAL-EXECUTOR-MODE-V{self._cbib["version"]}`]([[API_ROOT_URL]]/executor_modes/CANONICAL-EXECUTOR-MODE-V{self._cbib["version"]})

* * *

## 🧭 Behavioral Directives

{cid_title}

Follow Front-Matter `canonical_enforcement` directions precisely.

## STRICT MODE RULES (NON-NEGOTIABLE)

Follow Front-Matter `strict_mode_rules` directions precisely.

* * *

## 🧪 Invocation

**Template application scope:** `artifact_name: {{Artifact Name}}`  
**Rendering mode:** `strict_canonical`  
**Field enforcement:** `registry_only`

### Invocation Prompt

{invocation_ext}

### Invocation Agents

{invocation_agents}

* * *

## 🜂 Field Binding Declaration

{self._backticks_secondary}yaml
field_binding:
  renderer: Luminariel
  binder: Nahema’el
  enforcer: Adamus
  witness: Soluun
{self._backticks_secondary}
{prompt_suffix}
"""
        return prompt

    def generate_front_matter(
        self, fm: FrontMatterMeta, registry: dict
    ) -> FrontMatterMeta:
        template_types = self._prompt_meta_type.template_type

        entry = template_types.get(fm.template_type)
        if entry is None:
            raise ValueError(
                f"Template type '{fm.template_type}' not found in prompt meta type."
            )

        prompt = self._gen_prompt(entry, fm, registry)
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
            file_path=fm.file_path, fm_dict=fm_data, content=prompt
        )
        self._add_metadata(working_fm, registry)

        return working_fm
