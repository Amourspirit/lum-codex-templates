from typing import Any

from src.template.front_mater_meta import FrontMatterMeta
from src.config.pkg_config import PkgConfig
from .verify_rules.verify_rules import VerifyRules
from ..util.result import Result


class VerifyMetaFields:
    def __init__(
        self,
        registry: dict[str, Any],
        fm: FrontMatterMeta,
    ):
        self.config = PkgConfig()

        self._registry = registry
        self._fm = fm

    def _get_filtered_required_fields(self) -> set[str]:
        required_fields: set[str] = set()
        fields: dict[str, dict[str, Any]] = self._registry.get("fields", {})
        for key, value in fields.items():
            required = value.get("required", False)
            if required:
                required_fields.add(key)
        return required_fields

    def _get_all_fields_filtered(self) -> set[str]:
        all_fields: set[str] = set()
        fields: dict[str, dict[str, Any]] = self._registry.get("fields", {})
        for key in fields.keys():
            all_fields.add(key)
        return all_fields

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

    def _get_field_py_type(self, field_name: str) -> tuple[type, str] | None:
        """
        Retrieves the Python type and an optional subtype string for a given field name.
        This method looks up the field in the metadata_fields dictionary. If the field exists
        and has a "type" key, it maps the type string to a corresponding Python type and
        subtype (if applicable) using a predefined type mapping. Supported types include
        basic types like str, int, bool, float, list, dict, and lists of those types.

        Args:
            field_name (str): The name of the field to retrieve the type for.

        Returns:
            tuple[type, str] | None: A tuple containing the Python type and a subtype string
            (which may be empty), or None if the field does not exist or has no type defined.
        """

        metadata_fields = self._registry.get("fields", {})
        field_info = metadata_fields.get(field_name)
        if not field_info:
            return None
        field_type_str = field_info.get("type")
        if not field_type_str:
            return None
        type_mapping = {
            "string": (str, ""),
            "integer": (int, ""),
            "boolean": (bool, ""),
            "str": (str, ""),
            "int": (int, ""),
            "bool": (bool, ""),
            "float": (float, ""),
            "number": (float, ""),
            "num": (float, ""),
            "list": (list, ""),
            "dict": (dict, ""),
            "object": (dict, ""),
            "list[string]": (list, "str"),
            "list[integer]": (list, "int"),
            "list[boolean]": (list, "bool"),
            "list[float]": (list, "float"),
            "list[str]": (list, "str"),
            "list[int]": (list, "int"),
            "list[bool]": (list, "bool"),
        }
        return type_mapping.get(field_type_str.lower())

    def _get_incorrect_type_fields(self, fm: FrontMatterMeta) -> dict[str, Any]:
        incorrect_types = {}
        for field_name in fm.frontmatter.keys():
            field_type_info = self._get_field_py_type(field_name)
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

    def verify(self) -> Result[dict[str, Any], None] | Result[None, Exception]:
        try:
            required_fields = self._get_filtered_required_fields()
            all_fields = self._get_all_fields_filtered()
            fm_fields = set(self._fm.frontmatter.keys())
            missing_fields = required_fields - fm_fields
            extra_fields = fm_fields - all_fields
            incorrect_type_fields = self._get_incorrect_type_fields(self._fm)
            result: dict[str, Any] = {
                "missing_fields": sorted(list(missing_fields)),
                "extra_fields": sorted(list(extra_fields)),
                "template_info": {
                    "template_type": self._fm.template_type,
                    "template_id": self._fm.get_field("template_id", ""),
                    "template_version": self._fm.get_field("template_version", ""),
                    "title": self._fm.get_field("title", ""),
                    "artifact_name": self._fm.get_field("artifact_name", ""),
                },
            }

            if incorrect_type_fields:
                result["incorrect_type_fields"] = incorrect_type_fields
            verify_rule_results = self._get_verify_rules(self._fm)
            if verify_rule_results:
                result["rule_errors"] = verify_rule_results
            return Result.success(result)
        except Exception as e:
            return Result.failure(e)
