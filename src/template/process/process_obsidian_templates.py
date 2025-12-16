import re
import tempfile
from typing import Any

from pathlib import Path
from ...config.pkg_config import PkgConfig
from ..obsidian_editor import ObsidianEditor
from ..front_mater_meta import FrontMatterMeta


class ProcessObsidianTemplates:
    def __init__(self):
        self.config = PkgConfig()
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._tmp_path = Path(self._tmp_dir.name)

    def _process_templates(
        self, tmp_dir: Path, key_values: dict[str, Any]
    ) -> list[FrontMatterMeta]:
        processed_templates = []
        for dir_name in self.config.template_dirs:
            dir_path = self.config.root_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                for file_path in dir_path.glob("*.md"):
                    fm_dict, content = ObsidianEditor().read_template(file_path)
                    clean_content = self.remove_line_comments(content)
                    clean_content = clean_content.lstrip()
                    if fm_dict is None:
                        print(f"Skipping file without frontmatter: {file_path.name}")
                        continue
                    print(f"Processing template: {file_path.name}")
                    fm = FrontMatterMeta.from_frontmatter_dict(
                        file_path, fm_dict, clean_content
                    )
                    if not fm.has_field("template_id"):
                        continue
                    for key, value in key_values.items():
                        fm.set_field(key, value)
                    new_file_path = tmp_dir / file_path.name
                    self.config.template_config.update_yaml_dict(fm.frontmatter)
                    self._add_template_fields_declared(fm)
                    # Force recalculation of SHA256 after frontmatter changes
                    # It is important that this comes after updating the frontmatter
                    fm.recompute_sha256()
                    ObsidianEditor().write_template(
                        new_file_path, fm.frontmatter, clean_content
                    )
                    processed_templates.append(
                        FrontMatterMeta.from_frontmatter_dict(
                            new_file_path, fm.frontmatter, clean_content
                        )
                    )
        return processed_templates

    def remove_line_comments(self, markdown_content: str) -> str:
        """
        Removes only those lines that START with ''.
        The line must contain ONLY the comment.
        """

        # Pattern explanation:
        # ^                 # Anchor to the beginning of a line (due to re.M)
        # \s* # Match zero or more whitespace characters (allows for indentation)
        # # Match the literal end of the comment
        # \s* # Match zero or more whitespace characters (trailing space)
        # $                 # Anchor to the end of a line (due to re.M)

        line_comment_pattern = re.compile(r"^<!--.*-->$", re.MULTILINE)

        # Replace the matching line (including the line break, implicitly handled by the line anchors)
        cleaned_content = line_comment_pattern.sub("", markdown_content)

        return cleaned_content

    def _add_template_fields_declared(self, template: FrontMatterMeta) -> None:
        fields = sorted(list(template.frontmatter.keys()))
        fields.pop(
            fields.index("template_fields_declared")
        ) if "template_fields_declared" in fields else None

        template.frontmatter["template_fields_declared"] = fields

    def process(self, key_values: dict[str, Any]) -> dict[str, FrontMatterMeta]:
        """Process templates by updating their frontmatter with the provided key-values.

        Args:
            key_values (dict[str, Any]): A dictionary of key-value pairs to update in the frontmatter.

        Returns:
            dict: Dictionary of file hash values as key and FrontMatterMeta a value
        """

        fms = self._process_templates(self._tmp_path, key_values)
        results: dict[str, FrontMatterMeta] = {}
        for fm in fms:
            results[fm.sha256] = fm
        return results

    def cleanup(self):
        self._tmp_dir.cleanup()
