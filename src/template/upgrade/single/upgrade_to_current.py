from pathlib import Path
import yaml
from ....config.pkg_config import PkgConfig
from typing import Any
from ...front_mater_meta import FrontMatterMeta
from ...process.read_obsidian_template_meta import (
    ReadObsidianTemplateMeta,
)
from ....builder.build_ver_mgr import BuildVerMgr
from ....util import file_util


class UpgradeToCurrent:
    """Upgrade template package to current version."""

    def __init__(self):
        self.config = PkgConfig()
        reader = ReadObsidianTemplateMeta()
        self._template_meta = reader.read_template_meta()

        rpt_dir = (
            self.config.root_path / self.config.pkg_out_dir / self.config.reports_dir
        )
        if not rpt_dir.exists():
            rpt_dir.mkdir(parents=True)
        self._current_version = self._get_current_version()
        self._templates_path = (
            self.config.root_path
            / self.config.pkg_out_dir
            / f"single-{self._current_version}"
        )
        self._dest_dir_template = (
            self.config.root_path / self.config.pkg_out_dir / self.config.upgrade_dir
        )
        if not self._dest_dir_template.exists():
            self._dest_dir_template.mkdir(parents=True)

        self._dest_dir_reports = (
            self.config.root_path / self.config.pkg_out_dir / self.config.reports_dir
        )
        if not self._dest_dir_reports.exists():
            self._dest_dir_reports.mkdir(parents=True)

    def _get_current_version(self) -> int:
        """Get the current version of the package."""
        build_ver_mgr = BuildVerMgr()
        return build_ver_mgr.get_saved_version()

    def _upgrade_template_specific_fields(
        self,
        fm_existing_template: FrontMatterMeta,
        fm_upgrade_template: FrontMatterMeta,
        required_fields: set[str],
    ) -> None:
        """
        Set the fields of the existing template to the fields of the current template

        Args:
            fm_existing_template (FrontMatterMeta): Existing template frontmatter meta
            fm_upgrade_template (FrontMatterMeta): Upgrade template frontmatter meta for dist/single-[VER] directory
        """
        # required_fields = self._get_filtered_required_fields(fm_existing_template)
        for field in required_fields:
            if not fm_upgrade_template.has_field(field):
                value = fm_existing_template.get_field(field)
                fm_upgrade_template.set_field(field, value)

        fields = set(
            [
                "template_category",
                "template_family",
                "template_filename",
                "template_hash",
                "template_name",
                "template_type",
                "template_version",
            ]
        )
        for field in fields:
            value = fm_existing_template.get_field(field)
            fm_upgrade_template.set_field(field, value)

        single_fields_omitted = self.config.templates_config_info.tci_items[
            fm_existing_template.template_type
        ].single_fields_omitted

        for field in single_fields_omitted:
            if fm_upgrade_template.has_field(field):
                fm_upgrade_template.remove_field(field)

    def _get_existing_frontmatter(self, template_type: str) -> FrontMatterMeta:
        """Get existing frontmatter meta from complete template file."""
        tci = self.config.templates_config_info.tci_items[template_type]
        file_name = f"{template_type}-template-v{tci.template_version}.md"

        template_path = self._templates_path / file_name
        fm = FrontMatterMeta(file_path=template_path)
        return fm

    def _get_output_file_name(self, fm: FrontMatterMeta) -> str:
        """Get output file name for upgraded template."""
        if fm.has_field("title"):
            valid_filename = file_util.get_valid_filename(fm.get_field("title"))
        elif fm.has_field("artifact_name"):
            valid_filename = file_util.get_valid_filename(fm.get_field("artifact_name"))
        else:
            valid_filename = f"{fm.template_type}-template-v{fm.template_version}"
        return valid_filename

    def _write_new_frontmatter(self, fm: FrontMatterMeta) -> None:
        """Write new frontmatter to template file."""

        new_file_name = self._get_output_file_name(fm)
        new_template_path = self._dest_dir_template / f"{new_file_name}.md"
        fm.write_template(new_template_path)

    def _write_report(self, fm: FrontMatterMeta, extra_fields: set[str]) -> None:
        new_file_name = self._get_output_file_name(fm)
        result: dict[str, Any] = {
            "template_info": {
                "template_type": fm.template_type,
                "template_id": fm.get_field("template_id", ""),
                "template_version": fm.get_field("template_version", ""),
                "title": fm.get_field("title", ""),
                "artifact_name": fm.get_field("artifact_name", ""),
            },
            "extra_fields": sorted(list(extra_fields)),
        }
        report_file_path = (
            self._dest_dir_reports / f"{new_file_name}_upgrade_report.yaml"
        )
        with open(report_file_path, "w", encoding="utf-8") as f:
            yaml.dump(result, f, sort_keys=False, encoding="utf-8")

    def _cleanup_upgrade_contents(self, fm: FrontMatterMeta) -> None:
        """Cleanup upgrade contents if needed."""
        # replace all --- lines in content with * * *
        content_lines = fm.content.splitlines()
        cleaned_lines = []
        for line in content_lines:
            if line.strip() == "---":
                cleaned_lines.append("* * *")
            else:
                cleaned_lines.append(line)
        fm.content = "\n".join(cleaned_lines)

    def upgrade(self, template_path: str | Path) -> None:
        """Perform upgrade steps to bring package to current version."""
        # Example upgrade step: create reports directory if it doesn't exist
        if not self._templates_path.exists():
            raise FileNotFoundError(
                f"Templates path {self._templates_path} does not exist."
            )

        tpl_path = Path(template_path)
        if not tpl_path.exists():
            raise FileNotFoundError(f"Template path {tpl_path} does not exist.")
        try:
            fm_upgrade_template = FrontMatterMeta(file_path=tpl_path)
            required_fields = self._get_filtered_required_fields(fm_upgrade_template)
            all_fields = self._get_all_fields_filtered(fm_upgrade_template)
            fm_fields = set(fm_upgrade_template.frontmatter.keys())
            extra_fields = fm_fields - all_fields
            if not fm_upgrade_template.template_type:
                raise ValueError(
                    f"Field template_type is not specified in frontmatter of {tpl_path}."
                )
            fm_existing_template = self._get_existing_frontmatter(
                fm_upgrade_template.template_type
            )
            self._cleanup_upgrade_contents(fm_upgrade_template)
            self._upgrade_template_specific_fields(
                fm_existing_template=fm_existing_template,
                fm_upgrade_template=fm_upgrade_template,
                required_fields=required_fields,
            )
            self._write_new_frontmatter(fm_upgrade_template)
            self._write_report(fm_upgrade_template, extra_fields)

        except Exception as e:
            raise ValueError(f"Error reading frontmatter from {tpl_path}: {e}")

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
