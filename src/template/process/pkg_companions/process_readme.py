from pathlib import Path
import yaml
from .protocol_process import ProtocolProcess
from ....config.pkg_config import PkgConfig
from ...front_mater_meta import FrontMatterMeta
from ...main_registery import MainRegistry


class ProcessReadme(ProtocolProcess):
    def __init__(self, worksapce_dir: Path | str, registry: MainRegistry):
        self._workspace_dir = Path(worksapce_dir)
        self._main_registry = registry
        self.config = PkgConfig()
        self.file_src = self.config.root_path / self.config.readme_src

    def _validate_tokens(self, kw: dict) -> None:
        required_tokens = set(
            ["DATE", "VER", "BATCH_HASH", "BUILDER_VER", "TEMPLATE_COUNT"]
        )
        for token in required_tokens:
            if token not in kw:
                raise ValueError(f"Missing required token: {token}")

    def _build_templates_block(self) -> list[dict]:
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
                            fm.template_id: {
                                "template_id": fm.template_id,
                                "canonical_template_sha256_hash": fm.sha256,
                                "template_type": fm.template_type,
                                "template_name": fm.template_name,
                                "template_category": fm.template_category,
                                "template_version": fm.template_version,
                                "declared_registry_id": self._main_registry.reg_id,
                                "declared_registry_version": self._main_registry.reg_version,
                                "mapped_registry": self._main_registry.reg_id,
                                "mapped_registry_minimum_version": self._main_registry.reg_version,
                                "file_name": file_path.name,
                            }
                        }
                    )
        return templates_block

    def _update_front_matter(self, fm: dict, kv: dict) -> None:
        lock_file_name = (
            f"{self.config.lock_file_name}-{kv['VER']}{self.config.lock_file_ext}"
        )
        fm["contract_source"] = lock_file_name

        batch_uid = f"{self.config.batch_prefix}-{kv['VER']}-{kv['BATCH_HASH']}"
        fm["batch_uid"] = batch_uid

        fm["batch_hash"] = kv["BATCH_HASH"]

        fm["package_name"] = f"{self.config.package_output_name}-{kv['VER']}"
        fm["package_version"] = str(kv["VER"])
        fm["builder_version"] = str(kv["BUILDER_VER"])
        fm["date_of_submission"] = kv["DATE"]
        fm["total_templates"] = kv["TEMPLATE_COUNT"]
        fm["registry_target"] = self._main_registry.reg_id
        fm["registry_target_version"] = f"v{self._main_registry.reg_version}"
        fm["declared_in"] = lock_file_name
        fm["lockfile_name"] = lock_file_name
        fm["bundle_manifest_file"] = (
            f"{self.config.template_manifest_name}-{kv['VER']}.yaml"
        )

        protocol_scroll_path = self.config.root_path / self.config.protocol_src
        if not protocol_scroll_path.exists():
            raise FileNotFoundError(
                f"Protocol scroll source file not found: {protocol_scroll_path}"
            )

        protocols_name = (
            f"{protocol_scroll_path.stem}-{kv['VER']}{protocol_scroll_path.suffix}"
        )
        fm["protocol_scrolls"] = [protocols_name]
        self.config.template_config.update_yaml_dict(fm)

    def _update_content(self, content: str, kv: dict) -> str:
        key_values = kv.copy()
        key_values["REG_VER"] = self._main_registry.reg_version
        s = content.lstrip()
        for key, value in key_values.items():
            s = s.replace(f"[{key}]", str(value))

        templates_block = self._build_templates_block()
        templates_yaml = yaml.safe_dump(
            templates_block,
            sort_keys=False,
            default_flow_style=False,
        )
        s = s.replace("[README_TEMPLATES_BLOCK]", templates_yaml, count=1)

        return s

    def process(self, tokens: dict) -> Path:
        """
        Process the README source file and return its content as a string.
        Args:
            tokens (dict): A dictionary of tokens to replace in the README.
        Returns:
            Path: The path to the processed README file.
        """
        if not self.file_src.exists():
            raise FileNotFoundError(f"README source file not found: {self.file_src}")

        self._validate_tokens(tokens)

        fm = FrontMatterMeta(self.file_src)
        self._update_front_matter(fm.frontmatter, tokens)
        fm.content = self._update_content(fm.content, tokens)

        file_path = self._workspace_dir / f"README-{tokens['VER']}.md"
        fm.write_template(file_path)
        return file_path

    def get_process_name(self) -> str:
        """
        Gets the process name for this instance

        Returns:
            str: Process Name
        """
        return "ProcessReadme"
