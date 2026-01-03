from pathlib import Path
from .protocol_verify_rule import ProtocolVerifyRule
from .rule_linked_nodes import LinkedNodesRule
from ....template.front_mater_meta import FrontMatterMeta
from ....util.result import Result
from ...verify_error import VerifyError


class VerifyRules:
    def __init__(self):
        self._processes: dict[str, ProtocolVerifyRule] = {}
        self._register_default_processes()

    def register_process(self, process: ProtocolVerifyRule) -> None:
        """Register a ProtocolTemplate with this processor.

        Args:
            process (ProtocolTemplate): The process instance to add to this processor. The object
                should implement the expected ProtocolTemplate interface.

        Returns:
            None
        """

        self._processes[process.get_field_name()] = process

    def validate(self, fm: FrontMatterMeta) -> dict[str, dict[str, str]]:
        """
        Validates the frontmatter keys against predefined processes.
        Iterates through the keys in the provided FrontMatterMeta object's frontmatter.
        For each key that has a corresponding process in self._processes, it validates
        the associated value using the process's validate method. If validation fails,
        the error message is recorded in the result dictionary.

        Args:
            fm (FrontMatterMeta): The frontmatter metadata object to validate.

        Returns:
            dict[str, str]: A dictionary where keys are frontmatter keys that failed
            validation, and values are the corresponding error messages as strings.
        """
        r_key = "Field Errors"
        result = {r_key: {}}
        fm_keys = fm.frontmatter.keys()
        for key in fm_keys:
            if key in self._processes:
                process = self._processes[key]
                value = fm.frontmatter[key]
                p_result = process.validate(value)
                if Result.is_failure(p_result):
                    if isinstance(p_result.error, VerifyError):
                        result[r_key][key] = p_result.error.errors
                    else:
                        result[r_key][key] = str(p_result.error)
        if not result[r_key]:
            return {}
        return result

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

    def unregister_process(self, process: ProtocolVerifyRule) -> None:
        """
        Unregister a process from the processor.
        Removes the first occurrence of the given process from the processor's internal list
        of registered processes.

        Args:
            process (ProtocolTemplate): The process instance to remove.

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

        if process.get_field_name() in self._processes:
            del self._processes[process.get_field_name()]

    def _register_default_processes(self) -> None:
        """Register the default set of processes with this processor."""

        self.register_process(LinkedNodesRule())

    @property
    def Count(self) -> int:
        """Get the count of registered processes.

        Returns:
            int: The number of processes currently registered in the processor.
        """

        return len(self._processes)
