import argparse
from typing import cast
from .protocol_subparser import ProtocolSubparser
from .rule_pkg_zip import RulePkgZip
from ..config.pkg_config import PkgConfig


class CmdProcessor:
    def __init__(self):
        self.parser = argparse.ArgumentParser()

        self._cmd_sub_parser = self.parser.add_subparsers(
            dest="command", required=False
        )
        self._processes: list[ProtocolSubparser] = []
        self._register_default_processes()

    def register_process(self, process: ProtocolSubparser) -> None:
        """Register a ProtocolSubparser with this processor.

        Args:
            process (ProtocolSubparser): The process instance to add to this processor. The object
                should implement the expected ProtocolSubparser interface.

        Returns:
            None

        Side effects:
            Appends the provided process to the processor's internal list of processes
            (self._processes), mutating the processor's state.

        Behavioral notes:
            - This method does not perform duplicate checks; calling code should handle deduplication
            if required.
            - No explicit validation of the process interface is performed here; callers are expected
            to supply a compatible object.
            - Not inherently thread-safe — if multiple threads may register processes concurrently,
            callers should synchronize access externally.
        """

        self._processes.append(process)

    def unregister_all(self) -> None:
        """Unregister all processes from the registry.
        Clears the internal _processes collection so that no previously
        registered processes are tracked by this processor. This operation
        is idempotent and returns None.

        Important:
        - This method only removes references from the registry and does not
            stop, terminate, or otherwise modify the underlying process objects.
        - If you need to perform cleanup or shutdown on the processes, do so
            before calling this method.
        - Callers should ensure proper synchronization if the registry may be
            accessed concurrently from multiple threads or tasks.
        Returns:
            None:
        """

        self._processes.clear()

    def unregister_process(self, process: ProtocolSubparser) -> None:
        """
                Unregister a process from the processor.
        Package build complete.
                Removes the first occurrence of the given process from the processor's internal list
                of registered processes.

                Args:
                    process (ProtocolSubparser): The process instance to remove.

                Returns:
                    None:

                Raises:
                    ValueError: If the process is not currently registered.

                Notes:
                    - Removal uses list.remove semantics, so equality (__eq__) is used to locate the
                    process; identity is not guaranteed unless equality is identity-based.
                    - This operation mutates the internal _processes list in place.
                    - The method is not thread-safe; synchronize externally if concurrent access is possible.
        """

        self._processes.remove(process)

    def _register_default_processes(self) -> None:
        pkg_zip = RulePkgZip(self._cmd_sub_parser)

        self.register_process(pkg_zip)

    def process(self) -> int:
        """Process CLI arguments and dispatch to the first matching registered process.

        This method:
        - Parses the program's command-line arguments using self.parser.parse_args().
        - Extracts a command string from args.command.
        - Iterates through the processes registered in self._processes in insertion order.
        - For the first process where process.is_match(cmd) returns True, calls that process.action(args)
            and returns whatever integer exit code it produces.
        - If no registered process matches the parsed command, prints parser help text and returns 1.

        Assumptions:
        - self.parser is an argparse.ArgumentParser (or compatible) instance.
        - Each entry in self._processes implements:
                - is_match(cmd: str) -> bool
                - action(args: argparse.Namespace) -> int
        - args.command is present (and castable to str) in the parsed namespace.

        Side effects and errors:
        - argparse.ArgumentParser.parse_args() may raise SystemExit for invalid arguments.
        - The method may print help text via self.parser.print_help().
        - Any exceptions raised by process.is_match() or process.action() are propagated.
        - The return value is intended to be an OS-style exit code (int).
        Returns:
                int: Exit code from the matched process.action or 1 if no match is found.
        """

        args = self.parser.parse_args()
        cmd = cast(str | None, args.command)
        if cmd is None:
            self.parser.print_help()
            return 1
        for process in self._processes:
            if process.is_match(cmd):
                result = process.action(args)
                if result == 0:
                    cfg = PkgConfig()
                    print("Package build complete. Output Folder:", cfg.pkg_out_dir)
                return result
        self.parser.print_help()
        return 1
