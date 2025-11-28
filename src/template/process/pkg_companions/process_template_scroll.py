from pathlib import Path
from .protocol_process import ProtocolProcess
from ....config.pkg_config import PkgConfig
from ...front_mater_meta import FrontMatterMeta
from ...main_registery import MainRegistry


class ProcessTemplateScroll(ProtocolProcess):
    def __init__(self, worksapce_dir: Path | str, registry: MainRegistry):
        self._workspace_dir = Path(worksapce_dir)
        self._main_registry = registry
        self.config = PkgConfig()
        self.file_src = self.config.root_path / self.config.protocol_src

    def _validate_tokens(self, kw: dict) -> None:
        required_tokens = set(["DATE", "VER", "BATCH_HASH", "BUILDER_VER"])
        for token in required_tokens:
            if token not in kw:
                raise ValueError(f"Missing required token: {token}")

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

        protocol_scroll_path = self.config.root_path / self.config.protocol_src
        if not protocol_scroll_path.exists():
            raise FileNotFoundError(
                f"Protocol scroll source file not found: {protocol_scroll_path}"
            )

        protocols_name = (
            f"{protocol_scroll_path.stem}-{kv['VER']}{protocol_scroll_path.suffix}"
        )
        fm["protocol_scrolls"] = [protocols_name]

    def _update_content(self, content: str, kv: dict) -> str:
        key_values = kv.copy()
        key_values["REG_VER"] = self._main_registry.reg_version
        s = content.lstrip()
        for key, value in key_values.items():
            s = s.replace(f"[{key}]", str(value))

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

        fm.file_path

        file_path = (
            self._workspace_dir
            / f"{self.file_src.stem}-{tokens['VER']}{self.file_src.suffix}"
        )
        fm.write_template(file_path)
        return file_path

    def get_process_name(self) -> str:
        """
        Gets the process name for this instance

        Returns:
            str: Process Name
        """
        return "ProcessTemplateScroll"
