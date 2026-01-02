from typing import Any, cast
from pathlib import Path
import yaml
from ..protocol_support import ProtocolSupport
from ...main_registry import MainRegistry
from ...front_mater_meta import FrontMatterMeta
from ..meta_helpers.prompt_meta_type import TemplateEntry
from .prompt_template_field_beings2 import PromptTemplateFieldBeings2


class PromptTemplateFieldBeingsCreate(PromptTemplateFieldBeings2, ProtocolSupport):
    # Creates prompts for template field beings in 'create' invocation mode.
    # See Metadata/template_field_being_map.yml
    # Template Types of the yml file that have a 'create' entry will be processed here.
    def __init__(self, registry: MainRegistry) -> None:
        super().__init__(registry)

    def _get_ced(
        self, entry: TemplateEntry, fm: FrontMatterMeta, tokens: dict
    ) -> dict[str, Any]:
        # return f"""## 🌀 Canonical Executor Declaration (CEIB-V{self.config.template_ceib_single.version})
        result = PromptTemplateFieldBeings2._get_ced(self, entry, fm, tokens)

        if "artifact_name" in result["data"]:
            del result["data"]["artifact_name"]
        if fm.has_field("certificate_type"):
            result["data"] = self._insert_at(
                result["data"], "certificate_type", fm.get_field("certificate_type"), 5
            )
        return result

    def _get_invocation_mode(self) -> str:
        return "create"

    def _get_invocation_ext(
        self, entry: TemplateEntry, fm: FrontMatterMeta, tokens: dict
    ) -> str:
        cde = self._get_ced(entry, fm, tokens)
        cid_title = cde["title"]
        cid_data = cde["data"]
        # convert cid_data to yaml block
        cid_yaml = yaml.dump(cid_data, sort_keys=False)
        assert entry.create is not None, "entry.create must not be None"
        return f"""I invoke **{self.config.template_ceib_single.executor_mode}-V{self.config.template_ceib_single.version}**  
of file `{self.config.template_ceib_single.executor_mode}-V{self.config.template_ceib_single.version}.md`  
and {entry.create.invocation.strip()} and apply template file `{fm.file_path.name}`  
with registry file `{fm.template_type}-template-v{fm.template_version}-registry.yml`  
to the created artifact under **full deterministic execution mode**.

---

{cid_title}

{self._backticks_secondary}yaml
{cid_yaml}
{self._backticks_secondary}

---

**Template application scope:** `template_application_scope: render_and_embed`
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
        prompt += f"\n\n{self._backticks_primary}"
        return prompt

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
            if not template_entry.has_create():
                continue
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
            / f"Single-{self.config.template_to_field_being_map_name}-create-{tokens['VER']}.md"
        )
