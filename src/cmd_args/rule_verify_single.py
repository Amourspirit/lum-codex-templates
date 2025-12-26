import argparse
from pathlib import Path
from xml.etree.ElementInclude import include
from .sub_parser_base import SubParserBase
from .sub_parser_args import SubParserArgs
from .protocol_subparser import ProtocolSubparser


class RuleVerifySingle(SubParserBase, ProtocolSubparser):
    def __init__(
        self, cmd_sub_parser: argparse._SubParsersAction[argparse.ArgumentParser]
    ):
        self._cmd_sub_parser = cmd_sub_parser

        self._cmd = "verify-single"
        self._sub_parser = self._cmd_sub_parser.add_parser(
            name=self._cmd, help="Verify templates as single template files."
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
        self._sub_parser.add_argument(
            "-m",
            "--missing-values",
            help="Include actual missing field values in the output.",
            required=False,
            default=False,
            action="store_true",
            dest="missing_values",
        )

    def is_match(self, command: str) -> bool:
        return command == self._cmd

    def action(self, args: argparse.Namespace) -> int:
        import yaml
        from ..verify.single.verify_meta_fields import VerifyMetaFields

        try:
            file = args.file
            # if file is relative path, make it relative to current working directory
            file_path = Path(file)
            if not file_path.is_absolute():
                file_path = Path.cwd() / file_path
            if not file_path.exists():
                print(f"File not found: {file_path}")
                return 1
            verify = VerifyMetaFields(include_actual_fields=args.missing_values)
            result = verify.verify_from_path(str(file_path))
            if "error" in result:
                print(f"Error during verification: {result['error']}")
                return 1
            missing = result.get("missing_fields", [])
            extra = result.get("extra_fields", [])
            print(f"Verification results for file: {file_path.name}")
            print("Template Info:")
            template_info = result["template_info"]
            for key, value in template_info.items():
                print(f"  {key}: {value}")
            if missing:
                print("Missing fields:")
                print()
                for field in missing:
                    print(f"  - {field}")
                print()
            else:
                print("No missing fields.")
            if extra:
                print("Extra fields:")
                print()
                for field in extra:
                    print(f"  - {field}")
                print()
            else:
                print("No extra fields.")
            if args.missing_values and "actual_missing" in result:
                if "found_fields" in result["actual_missing"]:
                    print("Actual missing field values:")
                    print()
                    s = yaml.dump(
                        result["actual_missing"]["found_fields"], sort_keys=False
                    )
                    print(s)
                    print()

        except Exception as e:
            print(f"Error during verification: {e}")
            return 1
        return 0
