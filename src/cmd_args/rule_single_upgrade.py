import argparse
from pathlib import Path
from .sub_parser_base import SubParserBase
from .sub_parser_args import SubParserArgs
from .protocol_subparser import ProtocolSubparser


class RuleSingleUpgrade(SubParserBase, ProtocolSubparser):
    def __init__(
        self, cmd_sub_parser: argparse._SubParsersAction[argparse.ArgumentParser]
    ):
        self._cmd_sub_parser = cmd_sub_parser

        self._cmd = "upgrade-single"
        self._sub_parser = self._cmd_sub_parser.add_parser(
            name=self._cmd, help="Upgrade templates as single template files."
        )

        args = SubParserArgs(sub_parser=self._sub_parser, command=self._cmd)
        super().__init__(args)
        self._add_arguments()

    def _add_arguments(self):
        self._sub_parser.add_argument(
            "-f",
            "--file",
            type=str,
            help="Path to the single template file to verify.",
            required=True,
            dest="file",
        )

    def is_match(self, command: str) -> bool:
        return command == self._cmd

    def action(self, args: argparse.Namespace) -> int:
        from ..template.upgrade.single.upgrade_to_current import UpgradeToCurrent

        try:
            file = args.file
            # if file is relative path, make it relative to current working directory
            file_path = Path(file)
            if not file_path.is_absolute():
                file_path = Path.cwd() / file_path
            if not file_path.exists():
                print(f"File not found: {file_path}")
                return 1
            upgrade = UpgradeToCurrent()
            upgrade.upgrade(file_path)

        except Exception as e:
            print(f"Error during verification: {e}")
            return 1
        return 0
