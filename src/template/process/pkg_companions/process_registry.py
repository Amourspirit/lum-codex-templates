from pathlib import Path
from .protocol_process import ProtocolProcess
from ....config.pkg_config import PkgConfig
from ...main_registery import MainRegistry


class ProcessRegistry(ProtocolProcess):
    def __init__(self, worksapce_dir: Path | str, registry: MainRegistry):
        self._workspace_dir = Path(worksapce_dir)
        self._main_registry = registry
        self.config = PkgConfig()
        self.file_src = self.config.root_path / self.config.reg_file

    def process(self, tokens: dict) -> Path:
        """
        Process the Registry source file and return its content as a string.
        Args:
            tokens (dict): A dictionary of tokens to replace in the README.
        Returns:
            Path: The path to the processed README file.
        """
        if not self.file_src.exists():
            raise FileNotFoundError(f"README source file not found: {self.file_src}")

        file_path = self._workspace_dir / self.file_src.name
        # copy source to destination
        with self.file_src.open("r", encoding="utf-8") as f_src:
            content = f_src.read()
        with file_path.open("w", encoding="utf-8") as f_dest:
            f_dest.write(content)
        return file_path

    def get_process_name(self) -> str:
        """
        Gets the process name for this instance

        Returns:
            str: Process Name
        """
        return "ProcessRegistry"
