from typing import Any
from pathlib import Path
from ....main_registry import MainRegistry
from ....front_mater_meta import FrontMatterMeta
from .enforcement_base import EnforcementBase
from .protocol_enforcement import ProtocolEnforcement


class EnforcementCanonicalExecutorModeReadme(EnforcementBase, ProtocolEnforcement):
    def __init__(
        self,
        working_dir: Path,
        main_registry: MainRegistry,
        templates_data: dict[str, FrontMatterMeta],
    ):
        super().__init__(working_dir, main_registry, templates_data)

    def _validate_tokens(self, tokens: dict[str, Any]) -> None:
        required_tokens = set(["DATE", "VER"])
        for token in required_tokens:
            if token not in tokens:
                raise ValueError(f"Missing required token: {token}")

    def process(self, tokens: dict[str, Any]) -> Path:
        self._validate_tokens(tokens)
        content = self._get_executor_md(tokens)
        p = self._write_file(tokens, content)
        return p

    def _write_file(self, tokens: dict[str, Any], content: str) -> Path:
        output_path = (
            self.working_dir
            / f"README-CANONICAL-EXECUTOR-V{self.config.template_ceib_single.version}.md"
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path

    def _get_template_types(self) -> list[str]:
        return list(self.templates_data.keys())

    def _get_executor_md(self, tokens: dict[str, Any]) -> str:
        template_types = self._get_template_types()
        template_types.append("etc.")
        tts = ", ".join(template_types)
        md = f"""---
executor_mode: CANONICAL-EXECUTOR-MODE-V{self.config.template_ceib_single.version}
version: \"{self.config.template_ceib_single.version}\"
originator: Soluun + Luminariel
created: {tokens["DATE"]}
purpose: >
  This invocation protocol transforms any template rendering process into a strict,
  file-governed execution environment that disables inference, memory contamination,
  or fallback logic. It guarantees that template and registry files govern all behavior,
  field validation, and output.

applies_to:
  - All Codex Template Types ({tts})
  - All registry-enforced canonical modes
  - All canonical rendering invocations

enforcement:
  - full file parsing of `template_file`
  - strict matching to `registry_file`
  - render only declared `template_body` sections
  - no use of memory-based `template_id`
  - abort on unresolved fields or missing blocks
---

## 🌀 Canonical Executor Invocation Block (CEIB-V{self.config.template_ceib_single.version})

```md
I invoke **CANONICAL-EXECUTOR-MODE-V{self.config.template_ceib_single.version}**
to apply template file `TEMPLATE_FILENAME.md`
with registry file `TEMPLATE_REGISTRY.yml`
under **full deterministic execution mode**.

**Template application scope:** `artifact_name: [Artifact Title]`
**Rendering mode:** `strict_canonical`
**Field enforcement:** `registry_only`
```

* * *

## ⚖️ Executor Configuration (YAML Mode)

```yaml
executor_mode: CANONICAL-EXECUTOR-MODE-V{self.config.template_ceib_single.version}
template_file: TEMPLATE_FILENAME.md
registry_file: TEMPLATE_REGISTRY.yml
artifact_name: [Artifact Title]
canonical_mode: true
template_strict_integrity: true
disable_template_id_reference: true
disable_memory_templates: true
forbid_inference: true
placeholder_resolution: true
abort_on_field_mismatch: true
abort_on_placeholder_failure: true
render_section_order: from_template_body
render_only_declared_sections: true
validate_fields_from_registry: true
field_diff_mode: strict
output_mode:
  - console
  - obsidian
  - mirrorwall
```

* * *

## 🔐 Enforcement Summary

- ✅ **No memory-based template shortcuts allowed**
- ✅ **No fallback inference from cached completions**
- ✅ **All required fields must appear and validate**
- ✅ **All unresolved placeholders must abort**
- ✅ **All markdown sections must render per template**
- ❌ Rendering aborts on:
  - missing required fields
  - unresolved placeholders
  - omitted markdown sections

* * *

## 🧪 Canonical Execution Audit Output

```yaml
executor_validation_report:
  template_applied: true
  template_hash_validated: true
  registry_fields_enforced: true
  missing_fields: []
  extra_fields: []
  unresolved_placeholders: []
  block_structure_match: true
  canonical_render_status: success
```

If render fails:

```yaml
canonical_render_status: failure
abort_reason: [field_mismatch, missing_block, placeholder_unresolved]
rendered_output: null
```

* * *

## 🌀 Ready for Invocation

To apply this executor mode:

1. Include this file in your invocation stack
2. Use `template_file` and `registry_file` directly
3. Do not use `template_id`
4. Confirm all placeholders resolve
5. Expect abort if structure or field rules are broken

"""
        return md
