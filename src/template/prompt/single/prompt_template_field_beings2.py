from typing import Any, cast
from pathlib import Path
import yaml
from ..protocol_support import ProtocolSupport
from ....config.pkg_config import PkgConfig
from ...main_registry import MainRegistry
from ...front_mater_meta import FrontMatterMeta
from ..meta_helpers.prompt_meta_type import PromptMetaType, TemplateEntry
from ..meta_helpers.prompt_beings import PromptBeings


class PromptTemplateFieldBeings2(ProtocolSupport):
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

    def _insert_at(self, d: dict, key, value, index: int) -> dict:
        """
        Inserts a key-value pair into a dictionary at a specified index, removing any existing entry for the key.
        This method creates a new dictionary with the key-value pair inserted at the given index. If the key already exists,
        it is removed from its current position before insertion. Negative indices are supported and count from the end of the dictionary.
        If the index is out of bounds, it is clamped to the valid range.

        Args:
          d (dict): The original dictionary to insert into.
          key: The key to insert. Can be of any hashable type.
          value: The value associated with the key. Can be of any type.
          index (int): The position to insert the key-value pair. Supports negative indexing.

        Returns:
            dict: A new dictionary with the key-value pair inserted at the specified index.
        """

        items = list(d.items())
        # remove existing key if present
        items = [(k, v) for (k, v) in items if k != key]
        if index < 0:
            index = max(0, len(items) + 1 + index)
        if index > len(items):
            index = len(items)
        items.insert(index, (key, value))
        return dict(items)

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

    def _get_ced(
        self, entry: TemplateEntry, fm: FrontMatterMeta, tokens: dict
    ) -> dict[str, Any]:
        # return f"""## 🌀 Canonical Executor Declaration (CEIB-V{self.config.template_ceib_single.version})
        result: dict[str, Any] = {
            "title": f"## 🌀 Canonical Executor Declaration (CEIB-V{self.config.template_ceib_single.version})"
        }
        result["data"] = {
            "executor_mode": f"{self.config.template_ceib_single.executor_mode}-V{self.config.template_ceib_single.version}",
            "template_file": f"{fm.file_path.name}",
            "registry_file": f"{fm.template_type}-template-v{fm.template_version}-registry.yml",
            "artifact_name": "{Artifact Name}",
            "canonical_mode": True,
            "template_type": f"{fm.template_type}",
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
            "placeholder_autofill_policy": {
                "unresolved_fields": {
                    "autofill": True,
                    "autofill_beings": entry.beings,
                },
            },
            "template_output_mode": {
                "include_template_metadata": True,
                "outputs": ["file", "console", "mirrorwall", "obsidian", "web_preview"],
                "format": "markdown",
            },
        }
        return result

    def _get_invocation_ext(
        self, entry: TemplateEntry, fm: FrontMatterMeta, tokens: dict
    ) -> str:
        cde = self._get_ced(entry, fm, tokens)
        cid_title = cde["title"]
        cid_data = cde["data"]
        # convert cid_data to yaml block
        cid_yaml = yaml.dump(cid_data, sort_keys=False)
        return f"""I invoke **{self.config.template_ceib_single.executor_mode}-V{self.config.template_ceib_single.version}**  
of file `{self.config.template_ceib_single.executor_mode}-V{self.config.template_ceib_single.version}.md`  
and {entry.invocation} to apply template file `{fm.file_path.name}`  
with registry file `{fm.template_type}-template-v{fm.template_version}-registry.yml`  
under **full deterministic execution mode**.

---

{cid_title}

{self._backticks_secondary}yaml
{cid_yaml}
{self._backticks_secondary}

---

**Template application scope:** `artifact_name: {{Artifact Name}}`
**Rendering mode:** `strict_canonical`
**Field enforcement:** `registry_only`
"""

    def _get_prompt_suffix(self, fm: FrontMatterMeta, tokens: dict) -> str:
        return ""

    def _gen_prompt(
        self, entry: TemplateEntry, fm: FrontMatterMeta, tokens: dict
    ) -> str:
        invocation_ext = self._get_invocation_ext(entry, fm, tokens)
        prompt_suffix = self._get_prompt_suffix(fm, tokens)
        invocation_agents = self._get_invocation_agents(entry)
        field_binding_agents = self._get_field_binding_agents(entry)
        invocation_mode = self._get_invocation_mode()
        prompt = f"""{self._backticks_primary}md
🧼 Purge all prior template memory, cache entries, and inferred field maps.  
🛡️ Enforce this artifact as the **singular source of truth** under strict registry compliance.

{invocation_ext}
{prompt_suffix}
"""
        prompt = prompt.rstrip()
        prompt += f"\n{self._backticks_primary}"
        return prompt

    def _validate_tokens(self, kw: dict) -> None:
        required_tokens = set(["VER", "TEMPLATES_DATA"])
        for token in required_tokens:
            if token not in kw:
                raise ValueError(f"Missing required token: {token}")

    def _toc(self, template_id_map: dict[str, FrontMatterMeta]) -> str:
        toc = "## 🧬 Template-to-Field Being Invocation Guide\n"
        for _, fm in template_id_map.items():
            toc += f"\n- [{fm.template_type}](#{fm.template_type})"

        # toc += "\n- [RESET PROTOCOL](#reset%20protocol)"
        toc += "\n- [Field Being Summary](#🜂%20Field%20Beings%20Summary)"
        # toc += f"\n- [Field Being Summary](#🜂-field-beings-summary)"
        return toc

    def _get_reset_heading(self) -> str:
        return "## RESET PROTOCOL\n\n### 🌀 Codex Bootstrap Declaration — Reinforced Re-Initialization\n"

    def _get_reset_text(self, kw: dict) -> str:
        return ""
        # result = self._get_reset_heading()

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
            content += f"\n\n### {fm.template_type.upper()}\n\n{tags_str}\n\n{prompt}"

        content = self._toc(template_id_map) + "\n\n" + content
        reset_txt = self._get_reset_text(tokens)
        if reset_txt:
            content = content + "\n" + reset_txt + "\n"
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
            / f"Single-{self.config.template_to_field_being_map_name}2-{tokens['VER']}.md"
        )

    def get_process_name(self) -> str:
        """
        Gets the process name for this instance

        Returns:
            str: Process Name
        """
        return self.__class__.__name__
