import argparse
from .sub_parser_base import SubParserBase
from .sub_parser_args import SubParserArgs
from .protocol_subparser import ProtocolSubparser


class RuleSingleTemplate(SubParserBase, ProtocolSubparser):
    def __init__(
        self, cmd_sub_parser: argparse._SubParsersAction[argparse.ArgumentParser]
    ):
        self._cmd_sub_parser = cmd_sub_parser

        self._cmd = "single"
        self._sub_parser = self._cmd_sub_parser.add_parser(
            name=self._cmd, help="Export templates as single template files."
        )

        args = SubParserArgs(sub_parser=self._sub_parser, command=self._cmd)
        super().__init__(args)
        self._add_arguments()

    def _add_arguments(self):
        self._sub_parser.add_argument(
            "-b",
            "--build",
            type=int,
            help="Specify the build version for the package. If not provided then the next available build version will be used.",
            default=0,
        )

    def is_match(self, command: str) -> bool:
        return command == self._cmd

    def action(self, args: argparse.Namespace) -> int:
        from ..builder.single_builder import SingleBuilder

        try:
            builder = SingleBuilder(build_version=args.build)
            builder.build_package()
            print("Package build complete.")
        except Exception as e:
            print(f"Error during package build: {e}")
            return 1
        return 0
