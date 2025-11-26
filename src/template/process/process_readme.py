from ...config.pkg_config import PkgConfig
from ...template.front_mater_meta import FrontMatterMeta


class ProcessReadme:
    def __init__(self, config: PkgConfig):
        self.config = config
        self.readme_src = config.readme_src

    def _build_readme_templates_block(self) -> list:
        templates_block = []
        for dir_name in self.config.template_dirs:
            dir_path = self.config.root_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                for file_path in dir_path.glob("*.md"):
                    fm = FrontMatterMeta(file_path)
                    if not fm.has_field("template_id"):
                        continue
                    templates_block.append(
                        {
                            "template_id": fm.template_id,
                            "template_type": fm.template_type,
                            "template_name": fm.template_name,
                            "template_category": fm.template_category,
                            "template_version": fm.template_version,
                            "declared_registry_id": fm.declared_registry_id,
                            "path": f"./{file_path.name}",
                            "fields": fm.get_keys(),
                        }
                    )
        return templates_block

    def process(self) -> str:
        """Process the README source file and return its content as a string."""
        readme_path = self.config.root_path / self.readme_src
        if not readme_path.exists():
            raise FileNotFoundError(f"README source file not found: {readme_path}")

        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        return content
