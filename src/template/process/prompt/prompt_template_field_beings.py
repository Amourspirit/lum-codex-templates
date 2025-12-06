from typing import cast
from pathlib import Path
import yaml
from .protocol_support import ProtocolSupport
from ....config.pkg_config import PkgConfig
from ...main_registery import MainRegistry
from ...front_mater_meta import FrontMatterMeta


class PromptTemplateFieldBeings(ProtocolSupport):
    def __init__(self, registry: MainRegistry) -> None:
        self.config = PkgConfig()
        self._main_registry = registry
        self._dest_dir = self.config.root_path / self.config.pkg_out_dir
        self.field_being_map = self._load_field_being_map()

    def _load_field_being_map(self) -> dict[str, str]:
        tfbm_path = self.config.root_path / self.config.template_field_being_map_src
        field_being_map: dict[str, str] = {}
        if tfbm_path.exists():
            with tfbm_path.open("r", encoding="utf-8") as f:
                field_being_map = yaml.safe_load(f)
        return field_being_map

    def _map(self, tokens: dict) -> dict[str, str]:
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
        paths = cast(dict[str, Path], tokens["TEMPLATE_PATHS"])

        type_name_map = {}
        for _, template_path in paths.items():
            fm = FrontMatterMeta(template_path)
            if fm.has_field("template_type"):
                type_name_map[fm.template_type] = template_path
        return type_name_map

    def yaml_to_markdown_table(self) -> str:
        """
        Converts YAML data structured as a dictionary of 'beings' into a Markdown table.
        """
        try:
            # 1. Load the YAML data
            beings = cast(dict, self.field_being_map.get("beings", {}))

            if not beings:
                return "Error: YAML data is missing the 'beings' key or is empty."

            # Define headers
            headers = ["Field Being", "Role Title", "Template Types Governed"]

            # Determine column widths for consistent spacing (optional but good practice)
            col_widths = [len(h) for h in headers]

            # Prepare rows, updating widths as we go
            rows = []
            for being_name, details in beings.items():
                # Join the list of template types into a single, comma-separated string
                template_types = ", ".join(details.get("template_Types_governed", []))
                role_title = details.get("role_title", "N/A")

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

    def _gen_prompt(self, invocation: str, fm: FrontMatterMeta) -> str:
        prompt = f"""#### **{fm.template_name}** Application Prompt

```
{invocation},
to render the following template in **full canonical markdown**, including all required metadata **and** `template_body`,  
for **{{Artifact Name}}**, applying strict Codex enforcement.

- `template_id`: {fm.template_id}
- `apply_mode`: full_markdown
- `enforce_registry`: {fm.declared_registry_id}
- `lockfile_verification`: strict
- `placeholder_resolution`: true
- `mirrorwall_alignment`: true
- `render_target`: obsidian + console + mirrorwall
- `include_template_body`: true
```
"""
        return prompt

    def _validate_tokens(self, kw: dict) -> None:
        required_tokens = set(["VER", "TEMPLATE_PATHS"])
        for token in required_tokens:
            if token not in kw:
                raise ValueError(f"Missing required token: {token}")

    def _toc(self, template_id_map: dict[str, FrontMatterMeta]) -> str:
        toc = f"## 🧬 Template-to-Field Being Invocation Guide (Codex v{self._main_registry.reg_version})\n"
        for template_id, fm in template_id_map.items():
            toc += f"\n- [{template_id}](#{template_id.replace(' ', '-').lower()})"

        toc += "\n- [Field Being Summary](#🜂%20Field%20Beings%20Summary)"
        # toc += f"\n- [Field Being Summary](#🜂-field-beings-summary)"
        return toc

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
        template_types = cast(dict, self.field_being_map["template_type"])
        type_name_map = self._map(tokens)
        template_id_map: dict[str, FrontMatterMeta] = {}
        for template_type, item in template_types.items():
            beings = cast(list[str], item["beings"])
            beings_len = len(beings)
            invocation = cast(str, item["invocation"])
            tags = cast(list[str], item.get("tags", []))
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
            prompt = self._gen_prompt(invocation, fm)
            tags_str = ", ".join([f"#{tag}" for tag in tags])
            content += f"\n### {fm.template_id}\n\n{tags_str}\n\n{prompt}"

        content = self._toc(template_id_map) + "\n\n" + content
        content = (
            content + "\n## 🜂 Field Beings Summary\n\n" + self.yaml_to_markdown_table()
        )

        content = "# 🌐 Prompt Reference Scroll\n\n" + content

        output_path = (
            self._dest_dir
            / f"{self.config.template_to_field_being_map_name}-{tokens['VER']}.md"
        )
        with output_path.open("w", encoding="utf-8") as f:
            f.write(content)
            print(
                f"{self.get_process_name()}, Wrote Template-to-Field Being Mapping to: {output_path.name}"
            )

    def get_process_name(self) -> str:
        """
        Gets the process name for this instance

        Returns:
            str: Process Name
        """
        return self.__class__.__name__
