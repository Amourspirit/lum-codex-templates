#!/usr/bin/env python3
import sys
import argparse

from src.builder.default_builder import DefaultBuilder
from src.cmd_args.cmd_processor import CmdProcessor


def main() -> int:
    cp = CmdProcessor()
    cp_result = cp.process()

    return cp_result
    parser = argparse.ArgumentParser(
        description="Build a Codex Template Package with metadata lockfile."
    )
    parser.add_argument(
        "version",
        type=str,
        help="The version string for the package being built (e.g., '1.0.0').",
    )
    args = parser.parse_args()

    build_version = args.version
    print(f"Building package version: {build_version}")

    builder = DefaultBuilder(build_version)
    builder.build_package()

    print("Package build complete.")


if __name__ == "__main__":
    # sys.argv.append("50")
    sys.exit(main())
