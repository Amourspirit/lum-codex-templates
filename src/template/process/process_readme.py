from ...config.pkg_config import PkgConfig
from ...template.front_mater_meta import FrontMatterMeta


class ProcessReadme:
    def __init__(self):
        self.config = PkgConfig()
        self.readme_src = self.config.root_path / self.config.readme_src

    def _build_readme_templates_block(self) -> list[dict]:
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
                            "mapped_registry": fm.mapped_registry,
                            "path": f"./{file_path.name}",
                        }
                    )
        return templates_block

    def process(self) -> str:
        """Process the README source file and return its content as a string."""
        if not self.readme_src.exists():
            raise FileNotFoundError(f"README source file not found: {self.readme_src}")

        with open(self.readme_src, "r", encoding="utf-8") as f:
            content = f.read()

        return content
