import argparse
from .sub_parser_base import SubParserBase
from .sub_parser_args import SubParserArgs
from .protocol_subparser import ProtocolSubparser


class RulePkgZip(SubParserBase, ProtocolSubparser):
    def __init__(
        self, cmd_sub_parser: argparse._SubParsersAction[argparse.ArgumentParser]
    ):
        self._cmd_sub_parser = cmd_sub_parser

        self._cmd = "pkg-zip"
        self._sub_parser = self._cmd_sub_parser.add_parser(
            name=self._cmd, help="Package and zip a Codex Template Package."
        )

        args = SubParserArgs(sub_parser=self._sub_parser, command=self._cmd)
        super().__init__(args)
        self._add_arguments()

    def _add_arguments(self):
        self._sub_parser.add_argument(
            "-n",
            "--no-path",
            action="store_false",
            help="Determines whether to include the full path in the zip file. By default, the full path is included.",
            default=True,
        )
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
        from ..builder.default_builder import DefaultBuilder

        try:
            builder = DefaultBuilder(build_version=args.build)
            builder.build_package()
            print("Package build complete.")
        except Exception as e:
            print(f"Error during package build: {e}")
            return 1
        return 0
