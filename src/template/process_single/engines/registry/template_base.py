from typing import Any
from pathlib import Path
import yaml
from ....main_registry import MainRegistry
from .....config.pkg_config import PkgConfig
from ....front_mater_meta import FrontMatterMeta


class TemplateBase:
    def __init__(
        self,
        working_dir: Path,
        main_registry: MainRegistry,
        templates_meta: dict[str, dict[str, Any]],
        template_front_matter: FrontMatterMeta,
    ):
        self.__working_dir = working_dir
        self.__main_registry = main_registry
        self.__config = PkgConfig()
        self.__meta = templates_meta.get(template_front_matter.template_type, {})
        self.__tci = self.config.templates_config_info.tci_items[
            template_front_matter.template_type
        ]
        self.__fm = self._get_filtered_front_matter(template_front_matter)

    def _get_filtered_front_matter(self, orig_fm: FrontMatterMeta) -> FrontMatterMeta:
        omitted_fields = self.tci.single_fields_omitted
        filtered_fm = {
            key: value
            for key, value in orig_fm.frontmatter.items()
            if key not in omitted_fields
        }
        fm = FrontMatterMeta.from_frontmatter_dict(
            file_path=orig_fm.file_path,
            fm_dict=filtered_fm,
            content=orig_fm.content,
        )
        return fm

    def _get_registry_fields(self) -> dict[str, Any]:
        metadata_fields = self.main_registry.metadata_fields
        autofill_fields = self._get_template_meta_fields("autofill_fields")
        required_fields = self._get_template_meta_fields("required_fields")
        deprecated_fields = self._get_template_meta_fields("deprecated_fields")
        result: dict[str, Any] = {}
        for key, _ in self.fm.frontmatter.items():
            if key in metadata_fields:
                if key in deprecated_fields:
                    continue
                item = {}
                item["type"] = metadata_fields[key].get("field_type", "string")
                item["nullable"] = metadata_fields[key].get("nullable", True)
                item["default_value"] = metadata_fields[key].get("default_value", None)
                item["status"] = metadata_fields[key].get("status", "active")
                item["plugin_groups"] = metadata_fields[key].get("plugin_groups", [])
                item["autofill"] = key in autofill_fields
                item["required"] = key in required_fields
                if "description" in metadata_fields[key]:
                    item["description"] = metadata_fields[key]["description"]
                if "field_lineage" in metadata_fields[key]:
                    item["field_lineage"] = metadata_fields[key]["field_lineage"]

                result[key] = item
        result["template_registry"] = {
            "type": "object",
            "nullable": False,
            "status": "active",
            "plugin_groups": ["template_registry_management"],
            "autofill": False,
            "required": True,
            "description": "The field value that connects the markdown template to this registry.",
        }
        return result

    def _get_template_meta_fields(self, key_name: str) -> set[str]:
        omitted_fields = self.tci.single_fields_omitted
        fields = self.template_meta.get(key_name, [])
        return {field for field in fields if field not in omitted_fields}

    def _process_common(self, tokens: dict[str, Any]) -> dict[str, Any]:
        # Placeholder for common processing logic
        result: dict[str, Any] = {"registry_role": "template_local_registry"}
        result["registry_id"] = (
            f"{self.tci.template_id}-V{self.tci.template_version}-REGISTRY"
        )
        result["registry_version"] = self.tci.template_version
        result["registry_scope"] = self.tci.template_type
        result["template_type"] = self.tci.template_type
        result["template_hash"] = self.fm.sha256
        result["template_filename"] = (
            f"{self.tci.template_type}-template-v{self.tci.template_version}.md"
        )
        result["template_version"] = self.tci.template_version
        # result["batch_number"] = str(self.main_registry.build_version)

        # ===============================
        # Global Enforcement Flags
        # ===============================
        result["canonical_mode"] = True
        result["template_strict_integrity"] = True
        result["fail_on_unknown_field"] = True
        result["fail_on_unresolved_field_placeholder"] = True
        result["allow_prompt_placeholders"] = True
        result["allow_inference"] = False
        result["fail_on_field_mismatch"] = True

        # ===============================
        # Template Hash Enforcement
        # ===============================
        result["template_hash_enforcement"] = {
            "field_name": "template_hash",
            "algorithm": "sha256",
            "hash_scope": {
                "include": ["yaml_frontmatter", "template_body"],
            },
            "exclude_fields": ["template_hash"],
        }
        # ===============================
        # Autofill Configuration
        # ===============================

        auto_fill_config = {
            "enabled": True,
            "behavior": {
                "unresolved_field": "fail",
                "unresolved_prompt": "flag",
                "inferred_value": "deny",
            },
        }
        allowed_agents = self._get_template_meta_fields("field_being_autofill_registry")
        auto_fill_config["allowed_agents"] = list(allowed_agents)
        result["autofill"] = auto_fill_config

        # ===============================
        # Placeholder Semantics
        # ===============================
        placeholder_rules = {
            "delimiters": {
                "open": self.config.template_config.placeholder["open"],
                "close": self.config.template_config.placeholder["close"],
            },
            "prefixes": {
                "field": {"required": True, "must_resolve": True},
                "prompt": {
                    "required": False,
                    "must_resolve": False,
                    "audit_only": True,
                },
            },
        }

        result["placeholder_rules"] = placeholder_rules

        # ===============================
        # Declared Field Rules
        # ===============================
        declared_field_rules = self._get_registry_fields()
        result["fields"] = declared_field_rules

        # ===============================
        # Conditional Blocks
        # ===============================

        # “If mirrorwall_status is set to 'embedded' during rendering,
        # then the following logic applies.”
        # What a conditional block does:

        # conditionals:
        #   mirrorwall_confirmation:
        #     condition: mirrorwall_status == "embedded"
        #     requires_fields:
        #       - embedding_date
        #       - mirrored_by
        #     else_behavior: allow

        # 🧭 Translates as:

        # * **Name:** `mirrorwall_confirmation` (for audit/debugging)
        # * **Trigger Condition:** Only applies if `mirrorwall_status == "embedded"` at render-time
        # * **Effect:** If the condition is true, then the fields:

        #   * `embedding_date`
        #   * `mirrored_by`

        #   …are **now required**. If they are missing, the render **must abort**.
        # * **Else Behavior:** If the condition is *not met* (e.g. status is `pending`, `draft`, or unset), the template:

        #   * **Allows render to proceed**
        #   * **Does not enforce** `embedding_date` or `mirrored_by`

        conditionals = {
            "mirrorwall_confirmation": {
                "condition": 'mirrorwall_status == "embedded"',
                "requires_fields": ["embedding_date", "mirrored_by"],
                "else_behavior": "allow",
            }
        }
        result["conditionals"] = conditionals

        # ===============================
        # Render Guarantees
        # ===============================

        render_contract = {
            "output_format": "markdown",
            "include_front_matter": True,
            "include_body": True,
            "strip_conditional_markers": True,
            "unresolved_prompt_behavior": "retain",
            "unresolved_field_behavior": "abort",
        }
        result["render_contract"] = render_contract

        # ===============================
        # Audit Output
        # ===============================
        audit_config = {
            "pre_check": {
                "field_audit_output": True,
                "field_audit_scope": [
                    "missing_fields",
                    "mismatched_types",
                    "registry_defaults_used",
                    "autofill_used",
                    "extra_fields_detected",
                ],
            },
            "violation": {
                "behavior": "abort",
                "scope": "immediate",
                "on_violation_return": {
                    "canonical_rendering_status": "aborted",
                    "autofill_misalignment_detected": True,
                    "registry_validation_status": "failed",
                    "template_family_enforcement_status": "failed",
                    "template_output_mode_status": "failed",
                },
            },
            "emit_on_render": True,
            "include": [
                "resolved_fields",
                "unresolved_prompts",
                "autofilled_fields",
                "conditional_paths_taken",
            ],
        }
        result["audit"] = audit_config
        return result

    def _write_yaml_file(self, data: dict[str, Any]) -> Path:
        output_path = (
            self.working_dir
            / f"{self.fm.template_type}-template-v{self.fm.template_version}-registry.yml"
        )
        with open(output_path, "w") as f:
            yaml.dump(data, f, sort_keys=False)
        # print(f"Generated registry file: {output_path.name}")
        return output_path

    @property
    def template_meta(self) -> dict[str, Any]:
        return self.__meta

    @property
    def config(self) -> PkgConfig:
        return self.__config

    @property
    def main_registry(self) -> MainRegistry:
        return self.__main_registry

    @property
    def tci(self):
        return self.__tci

    @property
    def fm(self) -> FrontMatterMeta:
        return self.__fm

    @property
    def working_dir(self) -> Path:
        return self.__working_dir
