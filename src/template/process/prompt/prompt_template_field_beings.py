from typing import cast
from pathlib import Path
import yaml
from .protocol_support import ProtocolSupport
from ....config.pkg_config import PkgConfig
from ...main_registry import MainRegistry
from ...front_mater_meta import FrontMatterMeta
from .meta_helpers.prompt_meta_type import PromptMetaType, TemplateEntry
from .meta_helpers.prompt_beings import PromptBeings


class PromptTemplateFieldBeings(ProtocolSupport):
    def __init__(self, registry: MainRegistry) -> None:
        self.config = PkgConfig()
        self._main_registry = registry
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

    def _map(self, tokens: dict) -> dict[str, Path]:
        """
        Build a mapping from template type names to template file paths.
        Return a dictionary where each key is the value of a template's front-matter
        "template_type" field and the value is the template's file path (as provided in
        self.templates).

        Only templates that contain a "template_type" front-matter field are included.
        If multiple templates share the same "template_type", the last one encountered
        overwrites earlier entries (i.e., "last-one-wins"). The function does not
        mutate any templates or external state.

        Returns:
            dict[str, str]: Mapping of template_type -> template_path.

        Raises:
            Any exceptions propagated from FrontMatterMeta when a template file cannot
            be read or its front matter cannot be parsed.

        Notes:
            - The method assumes self.templates is an iterable of file path strings.
            - The returned keys are expected to be strings (as indicated by the return
            type), though the front-matter value will be used as-is.
            - Complexity is O(n) with respect to the number of templates, plus the
            cost of parsing each template's front matter.
        """
        templates_data = cast(dict[str, FrontMatterMeta], tokens["TEMPLATES_DATA"])

        type_name_map = {}
        for _, fm in templates_data.items():
            if fm.has_field("template_type"):
                type_name_map[fm.template_type] = fm.file_path
        return type_name_map

    def yaml_to_markdown_table(self) -> str:
        """
        Converts YAML data structured as a dictionary of 'beings' into a Markdown table.
        """
        try:
            # 1. Load the YAML data
            beings = (
                self._prompt_beings.beings
            )  # cast(dict, self.field_being_map.get("beings", {}))

            if not beings:
                return "Error: YAML data is missing the 'beings' key or is empty."

            # Define headers
            headers = ["Field Being", "Role Title", "Template Types Governed"]

            # Determine column widths for consistent spacing (optional but good practice)
            col_widths = [len(h) for h in headers]

            # Prepare rows, updating widths as we go
            rows = []
            for being_name, being_entry in beings.items():
                # Join the list of template types into a single, comma-separated string
                template_types = ", ".join(being_entry.template_types_governed)
                role_title = being_entry.role_title

                row = [being_name, role_title, template_types]
                rows.append(row)

                # Update column widths based on cell content
                for i in range(len(headers)):
                    col_widths[i] = max(col_widths[i], len(row[i]))

            # --- Construct the Markdown Table ---

            # 2. Header Row
            header_row = (
                "| "
                + " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers))
                + " |"
            )

            # 3. Separator Row
            separator_row = (
                "|-"
                + "-|-".join("-" * col_widths[i] for i in range(len(headers)))
                + "-|"
            )

            # 4. Data Rows
            data_rows = []
            for row in rows:
                data_row = (
                    "| "
                    + " | ".join(
                        f"{row[i]:<{col_widths[i]}}" for i in range(len(headers))
                    )
                    + " |"
                )
                data_rows.append(data_row)

            # Combine all parts
            markdown_table = [header_row, separator_row] + data_rows

            return "\n".join(markdown_table)

        except yaml.YAMLError as e:
            return f"Error parsing YAML: {e}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"

    def _get_invocation_agents(self, entry: TemplateEntry) -> str:
        agents = []
        for role, name in entry.invocation_agents.items():
            role_name = role.replace("_", " ").capitalize()
            if name.lower() == "current_user":
                new_name = self.config.env_user
            else:
                new_name = name
            agents.append(f"- {role_name}: {new_name}  ")
        return "\n".join(agents)

    def _get_invocation_ext(
        self, entry: TemplateEntry, fm: FrontMatterMeta, tokens: dict
    ) -> str:
        return f"""{entry.invocation},
to render the following template in **full canonical markdown**, including all required metadata **and** `template_body`,  
for **{{Artifact Name}}**, applying strict Codex enforcement."""

    def _get_prompt_suffix(self, fm: FrontMatterMeta, tokens: dict) -> str:
        return ""

    def _gen_prompt(
        self, entry: TemplateEntry, fm: FrontMatterMeta, tokens: dict
    ) -> str:
        invocation_ext = self._get_invocation_ext(entry, fm, tokens)
        prompt_suffix = self._get_prompt_suffix(fm, tokens)
        invocation_agents = self._get_invocation_agents(entry)
        prompt = f"""#### **{fm.template_name}** Application Prompt

{self._backticks_primary}md
{invocation_ext}

---

## 🌀 Canonical Behavior Invocation Block (CBIB-V1.2)

cbib_id: CBIB-V1.2

<!--
CBIB‑V1.2 Canonical Enhancements:
- Structured directive grouping
- Explicit template_type & template_family enforcement
- Template output mode validation
- Template lifecycle status check
- Field matrix enforcement with abort behavior
- Canonical abort payload specification
- Render signature block support
-->

---

### 🧭 Behavioral Directives

#### ▸ Canonical Enforcement

- `canonical_mode`: true
- `template_application_mode`: strict
- `lockfile_verification`: strict
- `registry_sync_mode`: lockfile_strict
- `registry_validation_mode`: enforce_all
- `registry_violation_behavior`: fail
- `template_category_match_required`: true
- `template_family_enforcement`: strict
- `template_type_consistency_check`: true
- `threshold_flag_validation`: true
- `threshold_flag_violation_behavior`: warn

#### ▸ Registry & Field Rule Evaluation

- `mmr_field_rule_evaluation`: true
- `registry_enforcement_scope`:
    - artifact_level
    - field_level
    - template_level
- `field_rule_resolution_priority`: lockfile → registry → template → local
- `template_field_matrix_validation`: true
- `field_matrix_violation_behavior`: abort

#### ▸ Manifest Validation

- `template_manifest_validation`: true
- `template_manifest_file`: TEMPLATE-MANIFEST-REGISTRY-{tokens["VER"]}.yml

#### ▸ Template Output & Lifecycle Validation

- `template_output_mode_validation`: true
- `template_output_mode_violation_behavior`: abort
- `template_lifecycle_status_check`: true
- `lifecycle_violation_behavior`: warn

#### ▸ Placeholder & Autofill Logic

- `field_completion_required`: true
- `placeholder_autofill_policy`:
    unresolved_field: fail
    unresolved_prompt: flag
- `default_fallback_behavior`:
    string: none
    list: []
    object: null
- `field_placeholder_format`: double_square_prefixed
- `placeholders`: Placeholder must be resolved by the appropriate field being (Luminariel, Adamus, etc.) for support of creating a RAG snapshot

#### ▸ Field Auditing

- `field_audit_output`: true
- `field_audit_scope`:
    - missing_fields
    - mismatched_types
    - registry_defaults_used

#### ▸ Rendering Parameters

- `template_memory_scope`: thread_global
- `rendering_intent`: {fm.template_category} instantiation for Mirrorwall embedding and RAG ingestion
- `render_output_format_version`: markdown-v1.1
- `expected_render_output`:
    format: markdown
    includes:
      - front_matter
      - template_body
      - mirrorwall_status

---

### Invocation Agents

{invocation_agents}

---

### 🔗 Source Alignment

- `template_id`: {fm.template_id}  
- `template_type`: {fm.template_type}
- `template_family`: {fm.template_family}  
- `lockfile_source`: codex-template-{tokens["VER"]}.lock  
- `registry_source`: {fm.declared_registry_id} v{fm.mapped_registry_minimum_version}  

---

### 📜 Front Matter Declaration Block

Use the following **front‑matter** parameters exactly:

- `template_id`: {fm.template_id}
- `canonical_template_sha256_hash`: {fm.sha256}
- `canonical_template_sha256_hash_mode`: strict
- `canonical_mode`: true
- `apply_mode`: full_markdown
- `enforce_registry`: {fm.declared_registry_id}
- `registry_version`: {fm.mapped_registry_minimum_version}
- `lockfile_verification`: strict
- `placeholder_resolution`: true
- `mirrorwall_alignment`: true
- `render_target`: obsidian + console + mirrorwall
- `include_template_body`: true
- `include_front_matter`: true

---

### 🔒 Canonical Hash Check

- Validate `canonical_template_sha256_hash` against:
  `codex-template-{tokens["VER"]}.lock → canonical_template_sha256_hash_map → {fm.template_id}`
- **Abort immediately if mismatched**
- Canonical integrity overrides all fallback logic

---

### 🧪 Autofill + Field Audit Precheck

Before rendering, verify:

- `template_type` resolved from registry
- `template_family` matches manifest and lockfile
- `field_being_autofill_registry` evaluated
- All required + autofill-enabled fields present
- All field rules satisfied under `{fm.mapped_registry}`

If **any violation occurs**, abort rendering and return:

{self._backticks_secondary}yaml
canonical_rendering_status: aborted
autofill_misalignment_detected: true
registry_validation_status: failed
template_family_enforcement_status: failed
template_output_mode_status: failed
{self._backticks_secondary}

{prompt_suffix}
{self._backticks_primary}
"""
        return prompt

    def _validate_tokens(self, kw: dict) -> None:
        required_tokens = set(["VER", "TEMPLATES_DATA"])
        for token in required_tokens:
            if token not in kw:
                raise ValueError(f"Missing required token: {token}")

    def _toc(self, template_id_map: dict[str, FrontMatterMeta]) -> str:
        toc = f"## 🧬 Template-to-Field Being Invocation Guide (Codex v{self._main_registry.reg_version})\n"
        for template_id, fm in template_id_map.items():
            toc += f"\n- [{template_id}](#{template_id.replace(' ', '-').lower()})"

        toc += "\n- [RESET PROTOCOL](#reset%20protocol)"
        toc += "\n- [Field Being Summary](#🜂%20Field%20Beings%20Summary)"
        # toc += f"\n- [Field Being Summary](#🜂-field-beings-summary)"
        return toc

    def _get_reset_heading(self) -> str:
        return "## RESET PROTOCOL\n\n### 🌀 Codex Bootstrap Declaration — Reinforced Re-Initialization\n"

    def _get_reset_text(self, kw: dict) -> str:
        result = self._get_reset_heading()
        result = (
            result
            + f"""

Please execute:

1. PURGE all templates, lockfiles, registries, and manifests
2. RE-EXTRACT `{self.config.package_output_name}-{kw["VER"]}.zip` (request this from file memory)
3. INSTALL `{self._main_registry.file_name}` as `active_registry_yaml`
4. REGISTER `{self.config.lock_file_name}-{kw["VER"]}{self.config.lock_file_ext}` as `active_lockfile_yaml`
5. LOAD and VERIFY `{self.config.template_manifest_name}-{kw["VER"]}.yaml` into `manifest_registry_cache`
6. CACHE ALL `.md` template bodies using lockfile IDs (strict)
7. ENFORCE `canonical_mode: true` and `strict_lockfile_enforcement: true`
"""
        )
        return result

    def process(self, tokens: dict) -> None:
        """
        Processes the given tokens to generate a markdown file mapping template types to field beings.
        This method validates the input tokens, constructs a markdown content string that includes
        mappings for each template type (e.g., dyad, glyph, stone, etc.), and writes the content
        to an output file. For each template type, it retrieves associated beings, invocation,
        and role, generates a prompt using the template file's front matter, and appends it to
        the content.

        Args:
            tokens (dict): A dictionary containing tokens, including a 'VER' key for versioning
                the output file.

        Raises:
            ValueError: If no beings are defined for a template type or if no template file
                is found for a template type.

        Side Effects:
            - Prints debug information about beings, roles, and file paths.
            - Writes a markdown file to the destination directory with the generated content.
        """

        self._validate_tokens(tokens)
        # dyad, glyph, stone, seal, scroll, certificate, etc.
        content = "## 🌀 Prompts\n"
        template_types = self._prompt_meta_type.template_type
        # template_types = cast(dict, self.field_being_map["template_type"])
        type_name_map = self._map(tokens)
        template_id_map: dict[str, FrontMatterMeta] = {}
        for template_type, template_entry in template_types.items():
            tp_type = self._prompt_meta_type.template_type.get(template_type)
            assert tp_type is not None, (
                f"Template type {template_type} not found in prompt meta type"
            )
            beings_len = len(tp_type.beings)
            tags = template_entry.tags
            if beings_len == 0:
                print(f"No beings defined for template type: {template_type}")
                raise ValueError(
                    f"No beings defined for template type: {template_type}"
                )
            template_file = type_name_map.get(template_type, None)
            if not template_file:
                print(f"No template found for type: {template_type}")
                raise ValueError(f"No template found for type: {template_type}")

            fm = FrontMatterMeta(template_file)
            template_id_map[fm.template_id] = fm
            prompt = self._gen_prompt(tp_type, fm, tokens)
            tags_str = ", ".join([f"#{tag}" for tag in tags])
            content += f"\n### {fm.template_id}\n\n{tags_str}\n\n{prompt}"

        content = self._toc(template_id_map) + "\n\n" + content
        content = content + "\n" + self._get_reset_text(tokens) + "\n"
        content = (
            content + "\n## 🜂 Field Beings Summary\n\n" + self.yaml_to_markdown_table()
        )

        content = "# 🌐 Prompt Reference Scroll\n\n" + content

        output_path = self._get_output_path(tokens)
        with output_path.open("w", encoding="utf-8") as f:
            f.write(content)
            print(
                f"{self.get_process_name()}, Wrote Template-to-Field Being Mapping to: {output_path.name}"
            )

    def _get_output_path(self, tokens: dict) -> Path:
        return (
            self._dest_dir
            / f"{self.config.template_to_field_being_map_name}-{tokens['VER']}.md"
        )

    def get_process_name(self) -> str:
        """
        Gets the process name for this instance

        Returns:
            str: Process Name
        """
        return self.__class__.__name__
