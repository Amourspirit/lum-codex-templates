from typing import Any
import yaml
from ...template.process.read_obsidian_template_meta import (
    ReadObsidianTemplateMeta,
)
from ...template.front_mater_meta import FrontMatterMeta
from ...config.pkg_config import PkgConfig
from ...builder.build_ver_mgr import BuildVerMgr
from ...template.obsidian_editor import ObsidianEditor
from ...template.main_registry import MainRegistry
from .verify_rules.verify_rules import VerifyRules


class VerifyMetaFields:
    def __init__(self, include_actual_fields: bool = False):
        self.config = PkgConfig()
        reader = ReadObsidianTemplateMeta()
        self._current_version = self._get_current_version()
        self._template_meta = reader.read_template_meta()
        self.include_actual_fields = include_actual_fields
        self._main_registry = MainRegistry(build_version=self._current_version)

    def _get_current_version(self) -> int:
        """Get the current version of the package."""
        build_ver_mgr = BuildVerMgr()
        return build_ver_mgr.get_saved_version()

    def _get_filtered_required_fields(self, fm: FrontMatterMeta) -> set[str]:
        if not fm.template_type:
            raise ValueError("Field template_type is not specified in frontmatter.")
        meta_dict = self._template_meta[fm.template_type]
        current_required_fields = set(meta_dict.get("required_fields", []))
        tci = self.config.templates_config_info.tci_items[fm.template_type]
        omitted_fields = tci.single_fields_omitted
        filtered = current_required_fields - set(omitted_fields)
        return filtered

    def _get_all_fields_filtered(self, fm: FrontMatterMeta) -> set[str]:
        meta_dict = self._template_meta[fm.template_type]
        current_autofill_fields = set(meta_dict.get("autofill_fields", []))
        current_required_fields = set(meta_dict.get("required_fields", []))
        current_hidden_fields = set(meta_dict.get("hidden_fields", []))
        optional_fields = set(meta_dict.get("optional_fields", []))
        all_fields = (
            current_autofill_fields
            | current_required_fields
            | current_hidden_fields
            | optional_fields
        )
        tci = self.config.templates_config_info.tci_items[fm.template_type]
        omitted_fields = tci.single_fields_omitted
        filtered = all_fields - set(omitted_fields)
        return filtered

    def verify_from_path(self, path: str) -> dict[str, Any]:
        fm = FrontMatterMeta(file_path=path)
        return self.verify(fm)

    def _get_actual_frontmatter(self, fm: FrontMatterMeta) -> FrontMatterMeta | None:
        """
        Gets the frontmatter from the previously built version of the template file
        if it exists. Returns None if not found or not applicable.

        Args:
            fm (FrontMatterMeta): The frontmatter meta object for the template file.

        Returns:
            FrontMatterMeta | None: The frontmatter meta from the built file, or None.
        """

        if not self.include_actual_fields:
            return None

        if not fm.template_type:
            raise ValueError("Field template_type is not specified in frontmatter.")

        current_version = self._current_version
        if current_version <= 0:
            return None

        destination_path = (
            self.config.root_path
            / self.config.pkg_out_dir
            / f"single-{current_version}"
        )
        if not destination_path.exists():
            return None

        tci = self.config.templates_config_info.tci_items[fm.template_type]
        file_name = f"{tci.template_type}-template-v{tci.template_version}.md"

        dest_file_path = destination_path / file_name
        if not dest_file_path.exists():
            return None
        editor = ObsidianEditor()
        frontmatter_dict, contents = editor.read_template(dest_file_path)
        if not frontmatter_dict:
            return None
        frontmatter = FrontMatterMeta.from_frontmatter_dict(
            file_path=dest_file_path,
            fm_dict=frontmatter_dict,
            content=contents,
        )
        return frontmatter

    def _get_actual_missing(
        self, fm: FrontMatterMeta, missing_fields: set[str]
    ) -> dict[str, Any]:
        """
        Compares the missing fields against the actual frontmatter fields
        from the built template file, if available.

        Args:
            fm (FrontMatterMeta): Frontmatter meta object of the template file.
            missing_fields (set[str]): Set of missing field names.

        Returns:
            dict: Dictionary containing found and missing fields.
        """
        actual_missing_values = {
            "found_fields": {},
            "missing_fields": set(),
        }
        for missing_field in missing_fields:
            if fm.has_field(missing_field):
                actual_missing_values["found_fields"][missing_field] = fm.get_field(
                    missing_field
                )
            else:
                actual_missing_values["missing_fields"].add(missing_field)
        return actual_missing_values

    def _verify_list_field_types(self, subtype: str, actual_value: Any) -> bool:
        if not isinstance(actual_value, list):
            return False
        type_map = {
            "str": str,
            "int": int,
            "bool": bool,
            "string": str,
            "integer": int,
            "boolean": bool,
            "float": float,
            "number": float,
            "num": float,
            "list": list,
            "dict": dict,
            "object": dict,
        }
        expected_subtype = type_map.get(subtype)
        if not expected_subtype:
            return True
        for item in actual_value:
            if not isinstance(item, expected_subtype):
                return False
        return True

    def _get_incorrect_type_fields(self, fm: FrontMatterMeta) -> dict[str, Any]:
        incorrect_types = {}
        for field_name in fm.frontmatter.keys():
            field_type_info = self._main_registry.get_field_py_type(field_name)
            if not field_type_info:
                continue
            expected_type, subtype = field_type_info
            actual_value = fm.get_field(field_name)
            if expected_type is list and subtype:
                if not self._verify_list_field_types(subtype, actual_value):
                    incorrect_types[field_name] = {
                        "expected_type": f"list[{subtype}]",
                        "actual_type": type(actual_value).__name__,
                    }
                continue
            if not isinstance(actual_value, expected_type):
                incorrect_types[field_name] = {
                    "expected_type": expected_type.__name__,
                    "actual_type": type(actual_value).__name__,
                }
        return incorrect_types

    def _get_verify_rules(self, fm: FrontMatterMeta) -> dict[str, Any]:
        verify_rules = VerifyRules()
        return verify_rules.validate(fm)

    def verify(self, fm: FrontMatterMeta) -> dict[str, Any]:
        try:
            required_fields = self._get_filtered_required_fields(fm)
            all_fields = self._get_all_fields_filtered(fm)
            fm_fields = set(fm.frontmatter.keys())
            missing_fields = required_fields - fm_fields
            extra_fields = fm_fields - all_fields
            incorrect_type_fields = self._get_incorrect_type_fields(fm)
            result: dict[str, Any] = {
                "missing_fields": sorted(list(missing_fields)),
                "extra_fields": sorted(list(extra_fields)),
                "template_info": {
                    "template_type": fm.template_type,
                    "template_id": fm.get_field("template_id", ""),
                    "template_version": fm.get_field("template_version", ""),
                    "title": fm.get_field("title", ""),
                    "artifact_name": fm.get_field("artifact_name", ""),
                },
            }
            if self.include_actual_fields and missing_fields:
                actual_fm = self._get_actual_frontmatter(fm)
                if actual_fm:
                    actual_missing = self._get_actual_missing(actual_fm, missing_fields)
                    result["actual_missing"] = actual_missing

            if incorrect_type_fields:
                result["incorrect_type_fields"] = incorrect_type_fields
            verify_rule_results = self._get_verify_rules(fm)
            if verify_rule_results:
                result["rule_errors"] = yaml.dump(verify_rule_results)
            return result
        except Exception as e:
            return {"error": str(e)}
