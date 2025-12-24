import tempfile
from pathlib import Path
from ..protocol_support import ProtocolSupport
from ....config.pkg_config import PkgConfig
from .prompt_template_field_beings import PromptTemplateFieldBeings
from .prompt_template_field_beings2 import PromptTemplateFieldBeings2
from .prompt_template_field_beings_upgrade import PromptTemplateFieldBeingsUpgrade
from .prompt_template_field_beings_upgrade2 import PromptTemplateFieldBeingsUpgrade2
from ...main_registry import MainRegistry


class SupportProcessor:
    """
    Manages and executes a collection of ProtocolSupport instances. Each process
    is responsible for processing a specific aspect of the package companions.

    Notes:
        - Writes lockfiles, readme, and protocol scroll to a temporary workspace directory.
        - Provides methods to register, unregister, and execute processes.
    """

    def __init__(self, registry: MainRegistry):
        self.config = PkgConfig()
        self._workspace_dir = self.config.root_path / self.config.pkg_out_dir
        self._main_registry = registry
        self._processes: list[ProtocolSupport] = []
        self._register_default_processes()

    def register_process(self, process: ProtocolSupport) -> None:
        """Register a ProtocolSupport with this processor.

        Args:
            process (ProtocolSupport): The process instance to add to this processor. The object
                should implement the expected ProtocolSupport interface.

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
            print(f"Processing Support Companion: {process.get_process_name()}")
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

    def unregister_process(self, process: ProtocolSupport) -> None:
        """
        Unregister a process from the processor.
        Removes the first occurrence of the given process from the processor's internal list
        of registered processes.

        Args:
            process (ProtocolSupport): The process instance to remove.

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
        prompt_template_field_beings = PromptTemplateFieldBeings(self._main_registry)

        self.register_process(prompt_template_field_beings)

        prompt_template_field_beings_upgrade = PromptTemplateFieldBeingsUpgrade(
            self._main_registry
        )
        self.register_process(prompt_template_field_beings_upgrade)

        prompt_template_field_beings2 = PromptTemplateFieldBeings2(self._main_registry)
        self.register_process(prompt_template_field_beings2)

        prompt_template_field_beings_upgrade2 = PromptTemplateFieldBeingsUpgrade2(
            self._main_registry
        )
        self.register_process(prompt_template_field_beings_upgrade2)
