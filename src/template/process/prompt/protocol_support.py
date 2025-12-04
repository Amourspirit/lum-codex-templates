from typing import Protocol
from ...main_registery import MainRegistry


class ProtocolSupport(Protocol):
    def __init__(self, registry: MainRegistry): ...
    def process(self, tokens: dict) -> None:
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