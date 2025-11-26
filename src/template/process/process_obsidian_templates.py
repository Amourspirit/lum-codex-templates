from collections.abc import Generator
from typing import Any
import tempfile
from pathlib import Path
from contextlib import contextmanager
from ...config.pkg_config import PkgConfig
from ..obsidian_editor import ObsidianEditor
from ..front_mater_meta import FrontMatterMeta


class ProcessObsidianTemplates:
    def __init__(self):
        self.config = PkgConfig()

    def _process_templates(
        self, tmp_dir: Path, key_values: dict[str, Any]
    ) -> list[Path]:
        processed_templates = []
        for dir_name in self.config.template_dirs:
            dir_path = self.config.root_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                for file_path in dir_path.glob("*.md"):
                    fm_dict, content = ObsidianEditor().read_template(file_path)
                    if fm_dict is None:
                        continue
                    fm = FrontMatterMeta.from_frontmatter_dict(file_path, fm_dict)
                    if not fm.has_field("template_id"):
                        continue
                    for key, value in key_values.items():
                        fm.set_field(key, value)
                    new_file_path = tmp_dir / file_path.name
                    ObsidianEditor().write_template(
                        new_file_path, fm.frontmatter, content
                    )
                    processed_templates.append(new_file_path)
        return processed_templates

    @contextmanager
    def process(self, key_values: dict[str, Any]) -> Generator[list[Path], Any, Any]:
        """Process templates by updating their frontmatter with the provided key-values.

        Args:
            key_values (dict[str, Any]): A dictionary of key-value pairs to update in the frontmatter.

        Returns:
            list: A list of Paths to the processed template files.
        """
        tmp_dir = None
        try:
            tmp_dir = tempfile.TemporaryDirectory()
            tmp_path = Path(tmp_dir.name)
            result = self._process_templates(tmp_path, key_values)
            yield result
        except Exception as e:
            raise e
        finally:
            # 4. Cleanup actions
            if tmp_dir is not None:
                tmp_dir.cleanup()
