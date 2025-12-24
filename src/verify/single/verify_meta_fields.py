from typing import Any
from ...template.process.read_obsidian_template_meta import (
    ReadObsidianTemplateMeta,
)
from ...template.front_mater_meta import FrontMatterMeta
from ...config.pkg_config import PkgConfig


class VerifyMetaFields:
    def __init__(self):
        self.config = PkgConfig()
        reader = ReadObsidianTemplateMeta()
        self._template_meta = reader.read_template_meta()

    def _get_filtered_required_fields(self, fm: FrontMatterMeta) -> set[str]:
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

    def verify(self, fm: FrontMatterMeta) -> dict[str, Any]:
        required_fields = self._get_filtered_required_fields(fm)
        all_fields = self._get_all_fields_filtered(fm)
        fm_fields = set(fm.frontmatter.keys())
        missing_fields = required_fields - fm_fields
        extra_fields = fm_fields - all_fields
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
        return result
