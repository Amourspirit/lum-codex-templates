import tempfile
from pathlib import Path
from .protocol_process import ProtocolProcess
from .process_readme import ProcessReadme
from .process_template_scroll import ProcessTemplateScroll
from .process_lock import ProcessLock
from .process_registry import ProcessRegistry
from ...main_registery import MainRegistry


class PkgCompanionsProcessor:
    """
    Manages and executes a collection of ProtocolProcess instances. Each process
    is responsible for processing a specific aspect of the package companions.

    Notes:
        - Writes lockfiles, readme, and protocol scroll to a temporary workspace directory.
        - Provides methods to register, unregister, and execute processes.
    """

    def __init__(self, registry: MainRegistry):
        self._workspace_dir = Path(tempfile.mkdtemp(prefix="pkg_companions_"))
        self._main_registry = registry
        self._processes: list[ProtocolProcess] = []
        self._register_default_processes()

    def register_process(self, process: ProtocolProcess) -> None:
        """Register a ProtocolProcess with this processor.

        Args:
            process (ProtocolProcess): The process instance to add to this processor. The object
                should implement the expected ProtocolProcess interface.

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

    def execute_all(self, tokens: dict) -> dict[str, Path]:
        """
        Execute all registered processes and return their result paths.
        Executes each process registered in self._processes by calling its
        process(tokens) method and collects the returned Path objects keyed by the
        process name (as provided by process.get_process_name()).

        Args:
            tokens (dict): A mapping of tokens (input data, configuration, or context)
                that is passed to each process when executed.

        Returns:
            dict[str, Path]: A dictionary mapping process names to the Path returned
            by the corresponding process. The dictionary insertion order follows the
            iteration order of self._processes.

        Raises:
            RuntimeError: If no processes are registered to execute (i.e., self._processes
                is empty), which may indicate cleanup() has been called previously.
            Exception: Any exception raised by an individual process during execution
                will propagate to the caller.

        Notes:
            - Each registered process is invoked once.
            - If multiple processes return the same process name, later results will
            overwrite earlier ones in the returned dictionary.
            - Side effects (file creation, network I/O, etc.) are performed by the
            individual processes and are not handled by this method.
        """

        if not self._processes:
            raise RuntimeError(
                "No processes registered to execute. Has cleanup been called?"
            )
        results = {}
        for process in self._processes:
            result_path = process.process(tokens)
            results[process.get_process_name()] = result_path
        return results

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

    def unregister_process(self, process: ProtocolProcess) -> None:
        """
        Unregister a process from the processor.
        Removes the first occurrence of the given process from the processor's internal list
        of registered processes.

        Args:
            process (ProtocolProcess): The process instance to remove.

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
        readme_processor = ProcessReadme(self._workspace_dir, self._main_registry)
        template_scroll_processor = ProcessTemplateScroll(
            self._workspace_dir, self._main_registry
        )
        lock_processor = ProcessLock(self._workspace_dir, self._main_registry)
        registry_processor = ProcessRegistry(self._workspace_dir, self._main_registry)

        self.register_process(readme_processor)
        self.register_process(template_scroll_processor)
        self.register_process(lock_processor)
        self.register_process(registry_processor)

    def cleanup(self) -> None:
        """
        Unregister all registered companions and remove the workspace directory and its contents.
        This method performs a cleanup sequence:
        1. Calls self.unregister_all() to deregister any runtime companions or handlers.
        2. If self._workspace_dir exists and is a directory, iterates over its immediate children:
            - Removes files via Path.unlink().
            - Removes directories (and their contents) via shutil.rmtree().
        3. Removes the workspace directory itself with Path.rmdir().

        Returns:
            None:

        Raises:
            FileNotFoundError: If the workspace directory or an item is deleted concurrently.
            PermissionError: If the process lacks permission to remove files or directories.
            OSError: For other I/O related errors (e.g., directory not empty due to concurrent writes).

        Notes:
            - The operation is destructive and will permanently delete files and directories within
            the workspace directory.
            - The method attempts to be idempotent: if the workspace directory does not exist,
            it performs no removals beyond unregistering.
            - Symlink handling follows pathlib and shutil semantics: a symlink to a file will be
            unlinked, while a symlink to a directory may be treated as a directory by is_dir()
            and passed to shutil.rmtree(); callers should be aware of this behavior.
            - The operation is not atomic; concurrent modifications to the workspace may cause
            exceptions or leave the workspace partially cleaned.
        """

        self.unregister_all()
        if self._workspace_dir.exists() and self._workspace_dir.is_dir():
            for item in self._workspace_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    # Handle nested directories if needed
                    import shutil

                    shutil.rmtree(item)
            self._workspace_dir.rmdir()
