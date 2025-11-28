from typing import Protocol
from pathlib import Path
from ...main_registery import MainRegistry


class ProtocolProcess(Protocol):
    def __init__(self, worksapce_dir: Path | str, registry: MainRegistry): ...
    def process(self, tokens: dict) -> Path:
        """Process method to be implemented by classes adhering to this protocol.

        Args:
            tokens (dict): A dictionary of tokens to be used in processing.

        Returns:
            Path: The path to the processed file.
        """
        ...

    def get_process_name(self) -> str:
        """
        Gets the process name for this instance

        Returns:
            str: Process Name
        """
        ...
