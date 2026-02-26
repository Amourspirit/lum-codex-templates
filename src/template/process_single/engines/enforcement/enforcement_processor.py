from pathlib import Path
from loguru import logger
from ....front_mater_meta import FrontMatterMeta
from ....main_registry import MainRegistry
from .protocol_enforcement import ProtocolEnforcement
from .enforcement_canonical_executor_mode_readme import (
    EnforcementCanonicalExecutorModeReadme,
)
from .enforcement_canonical_executor_mode import EnforcementCanonicalExecutorMode


class EnforcementProcessor:
    """
    Manages and executes a collection of ProtocolEnforcement instances. Each process
    is responsible for processing a specific aspect of the package companions.

    Notes:
        - Writes template registry workspace directory.
        - Provides methods to register, unregister, and execute processes.
    """

    def __init__(
        self,
        workspace_dir: Path,
        registry: MainRegistry,
        templates_data: dict[str, FrontMatterMeta],
    ):
        self._workspace_dir = workspace_dir
        self._main_registry = registry
        self._processes: list[ProtocolEnforcement] = []
        self._templates_data = templates_data
        try:
            self._register_default_processes()
        except Exception as e:
            logger.error("Error initializing EnforcementProcessor: {error}", error=e)
            raise

    def register_process(self, process: ProtocolEnforcement) -> None:
        """Register a ProtocolEnforcement with this processor.

        Args:
            process (ProtocolEnforcement): The process instance to add to this processor. The object
                should implement the expected ProtocolEnforcement interface.

        Returns:
            None
        """

        self._processes.append(process)

    def execute_all(self, tokens: dict) -> list[Path]:
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
        try:
            if not self._processes:
                raise RuntimeError(
                    "No processes registered to execute. Has cleanup been called?"
                )
            results = []
            for process in self._processes:
                result_path = process.process(tokens)
                results.append(result_path)
                print(f"Processed Enforcement: {result_path.name}")
            return results
        except Exception as e:
            logger.error(
                "Error executing processes in EnforcementProcessor: {error}", error=e
            )
            raise

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

    def unregister_process(self, process: ProtocolEnforcement) -> None:
        """
        Unregister a process from the processor.
        Removes the first occurrence of the given process from the processor's internal list
        of registered processes.

        Args:
            process (ProtocolEnforcement): The process instance to remove.

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
        enforcement_ceemr = EnforcementCanonicalExecutorModeReadme(
            working_dir=self._workspace_dir,
            main_registry=self._main_registry,
            templates_data=self._templates_data,
        )
        self.register_process(enforcement_ceemr)
        enforcement_ceem = EnforcementCanonicalExecutorMode(
            working_dir=self._workspace_dir,
            main_registry=self._main_registry,
            templates_data=self._templates_data,
        )
        self.register_process(enforcement_ceem)

    @property
    def Count(self) -> int:
        """Get the count of registered processes.

        Returns:
            int: The number of processes currently registered in the processor.
        """

        return len(self._processes)
