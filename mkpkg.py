#!/usr/bin/env python3
import sys
from src.cmd_args.cmd_processor import CmdProcessor


def main() -> int:
    try:
        cp = CmdProcessor()
        cp_result = cp.process()
        return cp_result
    except Exception as e:
        print(e)
    return 1


if __name__ == "__main__":
    # sys.argv.append("single")
    # sys.argv.append("pkg-zip")
    # sys.argv.append("-b")
    # sys.argv.append("85")
    #
    # sys.argv.append("verify-single")
    # sys.argv.append("-f")
    # sys.argv.append("tmp/verify.md")
    # sys.argv.append("-m")
    #
    # sys.argv.append("upgrade-single")
    # sys.argv.append("-f")
    # sys.argv.append("tmp/upgrade.md")
    #
    # sys.argv.append("clean-single")
    # sys.argv.append("-f")
    # sys.argv.append("tmp/upgraded.md")

    # install-api -b 84 -t glyph
    # sys.argv.append("install-api")
    # sys.argv.append("-b")
    # sys.argv.append("84")
    # sys.argv.append("-t")
    # sys.argv.append("glyph")
    sys.exit(main())
