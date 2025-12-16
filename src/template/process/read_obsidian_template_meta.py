from typing import cast, Any
from pathlib import Path
import yaml
from ...config.pkg_config import PkgConfig


class ReadObsidianTemplateMeta:
    def __init__(self):
        self.config = PkgConfig()
        self.template_meta_dir = Path(
            self.config.root_path / self.config.template_meta_dir
        )

    def read_template_meta(self) -> dict[str, dict[str, Any]]:
        """
        Reads the yaml metadata for all templates in the template meta directory and sub-directories.

        Raises:
            ValueError: If duplicate template types are found.

        Returns:
            dict[str, dict[str, Any]]: A dictionary mapping template types to their metadata dictionaries
        """
        results: dict[str, dict[str, Any]] = {}
        if self.template_meta_dir.exists() and self.template_meta_dir.is_dir():
            for file_path in self.template_meta_dir.rglob("*.yml"):
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        meta_dict = cast(dict, yaml.safe_load(f))
                        template_meta = cast(dict, meta_dict.get("template_meta", {}))
                        if "template_type" not in template_meta:
                            print(
                                f"Missing 'template_type' in meta file: {file_path.name}"
                            )
                            continue
                        template_type = cast(str, template_meta["template_type"])
                        if template_type in results:
                            raise ValueError(
                                f"Duplicate template_type '{template_type}' found in file: {file_path.name}"
                            )
                        results[template_type] = {}
                        results[template_type].update(template_meta)
                    except yaml.YAMLError as e:
                        print(f"Error reading YAML file {file_path.name}: {e}")
        return results
