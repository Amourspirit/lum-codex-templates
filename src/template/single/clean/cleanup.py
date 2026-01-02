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
from ...main_registry import MainRegistry
from ...process.process_obsidian_templates import ProcessObsidianTemplates


class Cleanup:
    """Upgrade template package to current version."""

    def __init__(self):
        self.config = PkgConfig()
        reader = ReadObsidianTemplateMeta()
        self._template_meta = reader.read_template_meta()

        self._current_version = self._get_current_version()
        rpt_dir = (
            self.config.root_path
            / self.config.pkg_out_dir
            / f"{self.config.reports_dir}-{self._current_version}"
        )
        if not rpt_dir.exists():
            rpt_dir.mkdir(parents=True)
        self._templates_path = (
            self.config.root_path
            / self.config.pkg_out_dir
            / f"single-{self._current_version}"
        )
        self._dest_dir_template = (
            self.config.root_path
            / self.config.pkg_out_dir
            / f"{self.config.upgrade_dir}-{self._current_version}"
        )
        if not self._dest_dir_template.exists():
            self._dest_dir_template.mkdir(parents=True)

        self._dest_dir_reports = (
            self.config.root_path
            / self.config.pkg_out_dir
            / f"{self.config.reports_dir}-{self._current_version}"
        )
        if not self._dest_dir_reports.exists():
            self._dest_dir_reports.mkdir(parents=True)
        self._main_registry = MainRegistry(build_version=self._current_version)

        process_templates = ProcessObsidianTemplates()

        self._obsidian_templates = process_templates.process(
            {
                "declared_registry_id": self._main_registry.reg_id,
                "declared_registry_version": self._main_registry.reg_version,
                "mapped_registry": self._main_registry.reg_id,
                "mapped_registry_minimum_version": self._main_registry.reg_version,
                "batch_number": str(self._current_version),
            }
        )

    def _get_obsidian_template_meta(self, template_type: str) -> FrontMatterMeta:
        """Get obsidian template meta for given template type."""
        for fm in self._obsidian_templates.values():
            if fm.template_type == template_type:
                return fm
        raise ValueError(
            f"Template type '{template_type}' not found in obsidian templates."
        )

    def _get_current_version(self) -> int:
        """Get the current version of the package."""
        build_ver_mgr = BuildVerMgr()
        return build_ver_mgr.get_saved_version()

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

    def _write_new_frontmatter(self, fm: FrontMatterMeta, output_name: str) -> None:
        """Write new frontmatter to template file."""
        if output_name:
            new_file_name = output_name
        else:
            new_file_name = self._get_output_file_name(fm)
        new_template_path = self._dest_dir_template / f"cleaned-{new_file_name}.md"
        fm.write_template(new_template_path)

    def _write_report(
        self, fm: FrontMatterMeta, removed: list[str], output_name: str
    ) -> None:
        if output_name:
            new_file_name = output_name
        else:
            new_file_name = self._get_output_file_name(fm)
        result: dict[str, Any] = {
            "template_info": {
                "template_type": fm.template_type,
                "template_id": fm.get_field("template_id", ""),
                "template_version": fm.get_field("template_version", ""),
                "title": fm.get_field("title", ""),
                "artifact_name": fm.get_field("artifact_name", ""),
            },
            "removed_fields": sorted(list(removed)),
        }
        report_file_path = (
            self._dest_dir_reports / f"{new_file_name}_cleaned_report.yaml"
        )
        with open(report_file_path, "w", encoding="utf-8") as f:
            yaml.dump(result, f, sort_keys=False, encoding="utf-8")

    def _cleanup_template_only_fields(self, fm: FrontMatterMeta) -> list[str]:
        """Cleanup template-only fields from frontmatter."""
        removed = []
        removal_fields = self.config.template_config.cleanup_fields_single
        for field in removal_fields:
            if fm.has_field(field):
                fm.remove_field(field)
                removed.append(field)
        return removed

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

    def _ensure_fields(
        self, fm_original: FrontMatterMeta, fm_obsidian: FrontMatterMeta
    ) -> None:
        fields = ["template_type", "template_id", "template_version"]
        for field in fields:
            if not fm_original.has_field(field) and fm_obsidian.has_field(field):
                fm_original.set_field(field, fm_obsidian.get_field(field))

    def clean(self, template_path: str | Path, output_name: str = "") -> None:
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
            fm_cleanup_template = FrontMatterMeta(file_path=tpl_path)
            if not fm_cleanup_template.template_type:
                raise ValueError(
                    f"Field template_type is not specified in frontmatter of {tpl_path}."
                )
            removed = self._cleanup_template_only_fields(fm_cleanup_template)
            self._cleanup_upgrade_contents(fm_cleanup_template)

            fm_obsidian = self._get_obsidian_template_meta(
                fm_cleanup_template.template_type
            )
            self._ensure_fields(fm_cleanup_template, fm_obsidian)

            self._write_new_frontmatter(fm_cleanup_template, output_name)
            self._write_report(fm_cleanup_template, removed, output_name)

        except Exception as e:
            raise ValueError(f"Error reading frontmatter from {tpl_path}: {e}")
