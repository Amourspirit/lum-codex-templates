from typing import cast
from .protocol_support import ProtocolSupport
from ....config.pkg_config import PkgConfig
from ...main_registery import MainRegistry


class PromptBootstrap(ProtocolSupport):
    def __init__(self, registry: MainRegistry):
        self._main_registry = registry
        self.config = PkgConfig()
        self._dest_dir = self.config.root_path / self.config.pkg_out_dir
        self.file_src = self.config.root_path / self.config.bootstrap_src

        if self._dest_dir.exists() is False:
            self._dest_dir.mkdir(parents=True, exist_ok=True)

    def _validate_tokens(self, kw: dict) -> None:
        required_tokens = set(["CURRENT_USER", "TEMPLATE_COUNT", "VER"])
        for token in required_tokens:
            if token not in kw:
                raise ValueError(f"Missing required token: {token}")

    def _update_content(self, content: str, kv: dict) -> str:
        key_values = kv.copy()
        key_values["REG_VER"] = self._main_registry.reg_version
        key_values["REG_ID"] = self._main_registry.reg_id
        key_values["MANIFFEST"] = self.config.template_manifest_name
        s = content.lstrip()
        for key, value in key_values.items():
            s = s.replace(f"[{key}]", str(value))
        return s

    def process(self, tokens: dict) -> None:
        """
        Process the Codex-Bootstrap-Declaration.md source file and write to dest dir.
        Args:
            tokens (dict): A dictionary of tokens to replace in the README.
        Returns:
            NOne:
        """
        if not self.file_src.exists():
            raise FileNotFoundError(f"{self.file_src.name} source file not found: {self.file_src}")

        self._validate_tokens(tokens)

        contents = self.file_src.read_text(encoding="utf-8")
        updated_contents = self._update_content(contents, tokens)

        ver = cast(int, tokens.get("VER"))
        out_file_name = f"{self.file_src.stem}-{ver}{self.file_src.suffix}"
        dest_file_path = self._dest_dir / out_file_name
        # write to destination
        dest_file_path.write_text(updated_contents, encoding="utf-8")
        print(f"{self.get_process_name()}, Wrote output to: {dest_file_path.name}")

    def get_process_name(self) -> str:
        """
        Gets the process name for this instance

        Returns:
            str: Process Name
        """
        return self.__class__.__name__