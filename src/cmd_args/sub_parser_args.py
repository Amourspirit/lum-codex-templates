import argparse
from dataclasses import dataclass


@dataclass
class SubParserArgs:
    """
    Data class to hold arguments for sub-parser init commands.
    """

    sub_parser: argparse.ArgumentParser
    command: str
