from typing import Any
from loguru import logger
from .protocol_verify_rule import ProtocolVerifyRule
from src.template.front_mater_meta import FrontMatterMeta
from .rule_linked_nodes import LinkedNodesRule
from .rule_allow_fields import RuleAllowFields
from .rule_boolean import RuleBoolean
from .rule_spoken_transmission import RuleSpokenTransmission
from .rule_field_being_requirement import RuleFieldBeingRequirement
from .rule_witness_requirement import RuleWitnessRequirement
from .rule_harmonic_safety_escalation import RuleHarmonicSafetyEscalation
from ...util.result import Result
from ...exceptions import (
    VerifyError,
    MissingKeyError,
    RequiredFieldMissingError,
    NullFieldError,
    SafetyAbortError,
    SafetyRestrictionError,
    SafetyWarningError,
)


class VerifyRules:
    def __init__(self):
        self._processes: dict[str, ProtocolVerifyRule] = {}
        self._register_default_processes()
        logger.debug("Initialized VerifyRules")

    def register_process(self, process: ProtocolVerifyRule) -> None:
        """Register a ProtocolTemplate with this processor.

        Args:
            process (ProtocolTemplate): The process instance to add to this processor. The object
                should implement the expected ProtocolTemplate interface.

        Returns:
            None
        """

        self._processes[process.get_field()] = process

    def _get_registry_field_types(self, registry: dict[str, Any]) -> dict[str, str]:
        """
        Extract and organize field types from a registry dictionary.
        This method processes a registry's field definitions and creates a mapping of
        field types to the field names that use each type.
        Args:
            registry (dict[str, Any]): A registry dictionary containing field definitions.
                Expected to have a "fields" key with nested dictionaries defining field
                properties including "type".
        Returns:
            dict[str, str]: A dictionary mapping field type names to sets of field names
                that use each type. Only includes fields that have a "type" property
                defined in their field_info dictionary.
        Example:
            >>> registry = {
            ...     "fields": {
            ...         "name": {"type": "string"},
            ...         "age": {"type": "integer"},
            ...         "email": {"type": "string"}
            ...     }
            ... }
            >>> result = self._get_registry_field_types(registry)
            >>> result
            {'string': {'name', 'email'}, 'integer': {'age'}}
        """

        reg_fields = registry.get("fields", {})
        field_types = {}
        for field_name, field_info in reg_fields.items():
            if isinstance(field_info, dict) and "type" in field_info:
                if field_info["type"] not in field_types:
                    field_types[field_info["type"]] = set()
                field_types[field_info["type"]].add(field_name)
        return field_types

    def _get_boolean_rules(
        self, registry: dict[str, Any]
    ) -> dict[str, ProtocolVerifyRule]:
        """
        Identify and return a dictionary of ProtocolVerifyRule instances that are of type RuleBoolean
        based on the field types defined in the registry.

        Args:
            registry (dict[str, Any]): A registry dictionary containing field definitions.
                Expected to have a "fields" key with nested dictionaries defining field
                properties including "type".

        Returns:
            dict[str, ProtocolVerifyRule]: A dictionary of ProtocolVerifyRule instances that are of type
                RuleBoolean. This dictionary is constructed by checking the field types in the registry
                and matching them to the registered processes in self._processes.
        """

        boolean_processes = {}
        field_types = self._get_registry_field_types(registry)

        key = "boolean"
        if key not in field_types:
            return boolean_processes

        boolean_fields = field_types[key]

        for field in boolean_fields:
            boolean_processes[field] = RuleBoolean(field)

        return boolean_processes

    def validate(
        self, fm: FrontMatterMeta, registry: dict[str, Any]
    ) -> dict[str, dict[str, list[str]]]:
        """
        Validates the frontmatter keys against predefined processes.
        Iterates through the keys in the provided FrontMatterMeta object's frontmatter.
        For each key that has a corresponding process in self._processes, it validates
        the associated value using the process's validate method. If validation fails,
        the error message is recorded in the result dictionary.

        Args:
            fm (FrontMatterMeta): The frontmatter metadata object to validate.
            registry (dict[str, Any]): The metadata registry to use for validation.

        Returns:
            dict[str, str]: A dictionary where keys are frontmatter keys that failed
            validation, and values are the corresponding error messages as strings.
            The dictionary is empty if all validations pass successfully.
            Warnings are included in the result under the key `Field Warnings` and errors under `Field Errors`.
        """
        field_errors_key = "Field Errors"
        field_warnings_key = "Field Warnings"
        result = {field_errors_key: {}, field_warnings_key: {}}
        boolean_rules = self._get_boolean_rules(registry)

        processes: dict[str, ProtocolVerifyRule] = {}
        processes.update(self._processes)
        processes.update(boolean_rules)

        # By using fm_and_global_keys it ensure rules are evaluated for all relevant keys,
        # even if they are not present in the frontmatter
        # (which allows for missing key errors to be properly captured and reported),
        # while also ensuring that we only evaluate rules for keys that are actually relevant to
        # the current frontmatter and registry context (since we take the union of the keys from both sources,
        # we won't accidentally evaluate rules for keys that are completely unrelated to the current validation scenario).
        # This can is also useful for rules that cover several related fields (multi-field rules).
        fm_and_global_keys = set(fm.frontmatter.keys()) | set(self._processes.keys())

        for key in fm_and_global_keys:
            if key in processes:
                process = processes[key]
                p_result = process.validate(fm, registry)
                if Result.is_failure(p_result):
                    error = p_result.error

                    # 1. SAFETY ABORT — highest priority, must return immediately
                    if isinstance(error, SafetyAbortError):
                        result[field_errors_key][key] = ["SAFETY ABORT: " + str(error)]
                        return result  # immediate stop

                    # 2. SAFETY RESTRICTION — hard error, but continue evaluating others
                    elif isinstance(error, SafetyRestrictionError):
                        result[field_errors_key][key] = [
                            "SAFETY RESTRICTION: " + str(error)
                        ]

                    # 3. SAFETY WARNING — soft warning
                    elif isinstance(error, SafetyWarningError):
                        result[field_warnings_key][key] = [
                            "SAFETY WARNING: " + str(error)
                        ]

                    # 4. MISSING KEY (treated as warning)
                    elif isinstance(error, MissingKeyError):
                        # missing key errors are considered to be warnings rather than hard errors,
                        # since they may be optional fields that are simply not present in the frontmatter
                        result[field_warnings_key][key] = error.errors

                    # 5. GENERAL VERIFY ERRORS (fallback)
                    # this must come last because VerifyError is a more general error type that could potentially include the others as subclasses,
                    # so we check for the more specific error types first before falling back to this more general case
                    elif isinstance(
                        error, (RequiredFieldMissingError, NullFieldError, VerifyError)
                    ):
                        result[field_errors_key][key] = error.errors

                    # 6. UNKNOWN / UNEXPECTED
                    else:
                        result[field_errors_key][key] = [str(error)]

        if not result[field_errors_key] and not result[field_warnings_key]:
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
        logger.debug("Unregistered all processes from VerifyRules")

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

        if process.get_field() in self._processes:
            del self._processes[process.get_field()]
            logger.debug(
                "Unregistered process {field} from VerifyRules",
                field=process.get_field(),
            )
        else:
            logger.warning(
                "Attempted to unregister process {field} which is not registered in VerifyRules",
                field=process.get_field(),
            )

    def _register_default_processes(self) -> None:
        """Register the default set of processes with this processor."""

        # boolean rules are dynamically generated based on the registry field types, so they are not registered here in the default processes

        self.register_process(LinkedNodesRule())
        self.register_process(RuleSpokenTransmission())
        self.register_process(RuleFieldBeingRequirement())
        self.register_process(RuleWitnessRequirement())
        self.register_process(RuleHarmonicSafetyEscalation())

        allowed_fields_all = (
            "tier",
            "artifact_elemental_resonance",
            "artifact_duration",
        )
        for field in allowed_fields_all:
            self.register_process(RuleAllowFields(field, "all"))

        allowed_fields_any = (
            "roles_authority",
            "roles_visibility",
            "roles_function",
            "roles_action",
        )
        for field in allowed_fields_any:
            self.register_process(RuleAllowFields(field, "any"))

    @property
    def Count(self) -> int:
        """Get the count of registered processes.

        Returns:
            int: The number of processes currently registered in the processor.
        """

        return len(self._processes)
