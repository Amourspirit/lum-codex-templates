import argparse
from typing import Protocol


class ProtocolSubparser(Protocol):
    def __init__(
        self, cmd_sub_parser: argparse._SubParsersAction[argparse.ArgumentParser]
    ): ...
    def action(self, args: argparse.Namespace) -> int: ...

    def is_match(self, command: str) -> bool: ...
