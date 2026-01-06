from __future__ import annotations
import argparse
from pathlib import Path
from .sub_parser_base import SubParserBase
from .sub_parser_args import SubParserArgs
from .protocol_subparser import ProtocolSubparser


class RuleInstallApi(SubParserBase, ProtocolSubparser):
    def __init__(
        self, cmd_sub_parser: argparse._SubParsersAction[argparse.ArgumentParser]
    ):
        self._cmd_sub_parser = cmd_sub_parser

        self._cmd = "install-api"
        self._sub_parser = self._cmd_sub_parser.add_parser(
            name=self._cmd, help="Install templates into api templates"
        )

        args = SubParserArgs(sub_parser=self._sub_parser, command=self._cmd)
        super().__init__(args)
        self._add_arguments()

    def _add_arguments(self):
        self._sub_parser.add_argument(
            "-t",
            "--template-type",
            type=str,
            help="The template type to install. If omitted all template types in the manifest will be installed.",
            required=False,
            dest="template_type",
            default=None,
        )
        self._sub_parser.add_argument(
            "-b",
            "--build",
            type=int,
            help="Specify the build version for the package. If not provided then the current build version will be used.",
            default=0,
        )

    def is_match(self, command: str) -> bool:
        return command == self._cmd

    def action(self, args: argparse.Namespace) -> int:
        from ..template.single.install.install_api import InstallAPI

        try:
            install_api = InstallAPI(build_number=args.build)
            if args.template_type:
                install_api.install_single(args.template_type)
            else:
                install_api.install()

        except Exception as e:
            print(f"Error during verification: {e}")
            return 1
        return 0
