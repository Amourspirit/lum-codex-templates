from typing import Any, TypeVar, cast, Generic
import inspect
from collections.abc import Callable
from loguru import logger
from api.lib.protocols import ProtocolRulesCache
from api.lib.upgrade.rules.shared_rule_cache import SharedRuleCache
from api.lib.verify.protocols import VerifyRuleFactory, ProtocolVerifyRule
from api.lib.verify.verify_result import VerifyResult
from api.lib.verify.verify_rules.types.phase_info import PhaseInfo
from src.template.front_mater_meta import FrontMatterMeta
from .rule_linked_nodes import LinkedNodesRule
from .rule_allow_fields import RuleAllowFields
from .rule_boolean import RuleBoolean
from .rule_spoken_transmission import RuleSpokenTransmission
from .rule_field_being_requirement import RuleFieldBeingRequirement
from .rule_witness_requirement import RuleWitnessRequirement
from .rule_harmonic_safety_escalation import RuleHarmonicSafetyEscalation
from ..exceptions import VerifyError

C = TypeVar("C")  # Cache type variable


class VerifySummary:
    """
    Structured result of running the UpgradeEngine.
    """

    def __init__(
        self,
        artifact: FrontMatterMeta,
        errors: dict[str, list[str]],
        warnings: dict[str, list[str]],
        logs: list[str],
    ):
        self.artifact = artifact
        self.errors = errors
        self.warnings = warnings
        self.logs = logs

    def is_success(self) -> bool:
        return not self.errors

    def __repr__(self) -> str:
        return (
            f"VerifySummary(errors={self.errors}, "
            f"warnings={self.warnings}, logs={self.logs})"
        )


class VerifyEngine(Generic[C]):
    def __init__(self, shared_cache: ProtocolRulesCache[C]):
        self._rules: dict[str, ProtocolVerifyRule] = {}
        self._shared_cache: ProtocolRulesCache[C] = shared_cache
        logger.debug("Initialized VerifyEngine")

    def required_params(self, callable_obj: Callable[..., Any]) -> tuple[str, ...]:
        """Return required parameter names for a callable."""
        sig = inspect.signature(callable_obj)
        names: list[str] = []
        for p in sig.parameters.values():
            if p.default is inspect.Signature.empty and p.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            ):
                names.append(p.name)
        return tuple(names)

    # --------------------------
    # Hooks (optional overrides for custom behavior)
    # --------------------------
    def before_all_rules(self):
        pass

    def after_each_rule(
        self,
        rule: ProtocolVerifyRule,
        result: VerifyResult[FrontMatterMeta, None] | VerifyResult[None, VerifyError],
    ):
        pass

    def after_all_rules(self, summary: VerifySummary):
        pass

    def _create_rule_instance(self, rule_cls: ProtocolVerifyRule) -> ProtocolVerifyRule:
        """
        Create a rule instance from either:
        - factory() -> ProtocolVerifyRule
        - factory(shared_cache) -> ProtocolVerifyRule
        """
        param_names = self.required_params(cast(Callable[..., Any], rule_cls))
        candidate: Any = None

        try:
            if all(name in param_names for name in ("shared_cache",)):
                candidate = cast(
                    Callable[[ProtocolRulesCache[C]], ProtocolVerifyRule], rule_cls
                )(self._shared_cache)

        except TypeError:
            candidate = None

        if candidate is None:
            candidate = cast(VerifyRuleFactory, rule_cls)()

        # Structural guard for clearer runtime errors.
        required = (
            "get_rule_id",
            "get_description",
            "RULE_ORDER",
            "should_run",
            "apply",
        )
        missing = [name for name in required if not hasattr(candidate, name)]
        if missing:
            raise TypeError(
                f"Registered rule factory did not produce a ProtocolUpgradeRule. Missing: {missing}"
            )

        return cast(ProtocolVerifyRule, candidate)

    # --------------------------
    # Severity routing
    # --------------------------
    def _route_severity(
        self,
        rule_id: str,
        result: VerifyResult[None, VerifyError],
        errors: dict[str, Any],
        warnings: dict[str, Any],
        logs: list[str],
    ) -> bool:
        # Optional human-readable message if payload is a string
        payload_info = (
            f" payload={result.payload!r}" if result.payload is not None else ""
        )

        error = result.error
        if result.is_warning():
            warnings.setdefault(rule_id, []).extend(error.errors)
            logs.append(f"[WARN] {rule_id}: {error.errors}{payload_info}")
            return False

        if result.is_error():
            errors.setdefault(rule_id, []).extend(error.errors)
            logs.append(f"[ERROR] {rule_id}: {error.errors}{payload_info}")
            return False

        if result.is_critical():
            errors.setdefault(rule_id, []).extend(error.errors)
            logs.append(f"[CRITICAL] {rule_id}: {error.errors}{payload_info}")
            return True  # HALT ENGINE

        # Safety fallback
        errors.setdefault(rule_id, []).extend(error.errors)
        logs.append(f"[ERROR] {rule_id}: {error.errors}{payload_info}")
        return False

    # --------------------------
    # Execution
    # --------------------------

    def apply(
        self,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> VerifySummary:

        self.reset()
        self.before_all_rules()

        boolean_rules = self._get_boolean_rules(registry)
        rules: dict[str, ProtocolVerifyRule] = {}
        rules.update(self._rules)
        rules.update(boolean_rules)

        # Deterministic ordering based on RULE_ORDER, default = 100
        ordered_rules = sorted(
            rules.values(), key=lambda r: getattr(r, "RULE_ORDER", lambda: 100)()
        )

        errors: dict[str, list[str]] = {}
        warnings: dict[str, list[str]] = {}
        logs: list[str] = []

        current_artifact = fm_template.copy()
        for rule in ordered_rules:
            # Rule applicability check

            should_run = rule.should_run(current_artifact, registry)
            if not should_run:
                logs.append(f"[SKIP] Rule {rule.get_rule_id()} (should_run=False)")
                continue

            # Execute rule
            try:
                result = rule.apply(
                    fm_template=current_artifact,
                    registry=registry,
                )

                if VerifyResult.is_failure(result):
                    critical = self._route_severity(
                        rule.get_rule_id(), result, errors, warnings, logs
                    )
                    if critical:
                        logs.append(
                            f"[CRITICAL] Rule {rule.get_rule_id()} encountered a critical error"
                        )
                        logger.error(
                            f"Critical error in rule {rule.get_rule_id()}: {result.error}"
                        )
                        break
                else:
                    # Rule succeeded — update artifact reference
                    current_artifact = result.data
                    logs.append(f"[OK] Rule {rule.get_rule_id()} applied successfully")

                self.after_each_rule(
                    rule, result
                )  # Placeholder for potential future use
            except Exception as ex:
                # Hard catch: rules should not break the engine
                errors.setdefault(rule.get_rule_id(), []).append(str(ex))
                logs.append(
                    f"[CRITICAL] Exception in rule {rule.get_rule_id()}: {str(ex)}"
                )

        summary = VerifySummary(
            artifact=current_artifact,
            errors=errors,
            warnings=warnings,
            logs=logs,
        )

        self.after_all_rules(summary)  # Placeholder for potential future use

        return summary

    def register_rule(self, rule_cls: Any) -> None:
        instance = self._create_rule_instance(rule_cls)
        self.register_rule_instance(instance)

    def register_rule_instance(self, instance: ProtocolVerifyRule) -> None:
        self._rules[instance.get_rule_id()] = instance
        logger.debug(f"Registered Upgrade Rule: {instance.get_rule_id()}")

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
            boolean_processes[field] = RuleBoolean(self._shared_cache, field)

        return boolean_processes

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

        self._rules.clear()
        logger.debug("Unregistered all processes from VerifyRules")

    def reset(self):
        self._shared_cache.clear()
        logger.debug("Reset UpgradeEngine state and cleared shared cache")

    def unregister_rule(self, rule: ProtocolVerifyRule) -> None:
        """
        Unregister a rule from the processor.
        Removes the first occurrence of the given rule from the processor's internal list
        of registered rules.

        Args:
            rule (ProtocolVerifyRule): The rule instance to remove.

        Returns:
            None:

        Raises:
            ValueError: If the rule is not currently registered.

        Notes:
            - Removal uses list.remove semantics, so equality (__eq__) is used to locate the
            rule; identity is not guaranteed unless equality is identity-based.
            - This operation mutates the internal _processes list in place.
            - The method is not thread-safe; synchronize externally if concurrent access is possible.
        """

        if rule.get_rule_id() in self._rules:
            del self._rules[rule.get_rule_id()]
            logger.debug(
                "Unregistered process {field} from VerifyRules",
                field=rule.get_rule_id(),
            )
        else:
            logger.warning(
                "Attempted to unregister process {field} which is not registered in VerifyRules",
                field=rule.get_rule_id(),
            )

    @property
    def count(self) -> int:
        """Get the count of registered processes.

        Returns:
            int: The number of processes currently registered in the processor.
        """

        return len(self._rules)

    @property
    def shared_cache(self) -> ProtocolRulesCache[C]:
        """Get the shared cache instance used by this processor.

        Returns:
            ProtocolRulesCache[C]: The shared cache instance that is passed to rules during instantiation.
        """

        return self._shared_cache


def create_default_verify_engine() -> VerifyEngine[PhaseInfo]:
    """
    Create and configure a default verify engine with standard rules.
    This function initializes a VerifyEngine instance parameterized with PhaseInfo
    and registers the default set of verify rules required for phase verification.

    Returns:
        VerifyEngine[PhaseInfo]: A configured verify engine instance with the
            RuleContinuumPhaseUpgrade rule registered and ready to process phase
            verification operations.

    Example:
        >>> engine = create_default_verify_engine()
        >>> # Engine is now ready to process verification operations
    """
    rules = (
        RuleFieldBeingRequirement,
        RuleHarmonicSafetyEscalation,
        LinkedNodesRule,
        RuleSpokenTransmission,
        RuleWitnessRequirement,
    )

    Engine = VerifyEngine[PhaseInfo]
    engine = Engine(shared_cache=SharedRuleCache())
    for rule_cls in rules:
        engine.register_rule(rule_cls)

    allowed_fields_all = (
        "tier",
        "artifact_elemental_resonance",
        "artifact_duration",
    )
    for field in allowed_fields_all:
        engine.register_rule_instance(
            RuleAllowFields(engine.shared_cache, field, "all")
        )

    allowed_fields_any = (
        "roles_authority",
        "roles_visibility",
        "roles_function",
        "roles_action",
    )
    for field in allowed_fields_any:
        engine.register_rule_instance(
            RuleAllowFields(engine.shared_cache, field, "any")
        )
    return engine
