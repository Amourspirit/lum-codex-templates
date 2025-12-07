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
    # sys.argv.append("pkg-zip")
    # sys.argv.append("-b")
    # sys.argv.append("57")
    sys.exit(main())
