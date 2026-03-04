from __future__ import annotations
from typing import Any, List, Dict, cast
from loguru import logger
from src.template.front_mater_meta import FrontMatterMeta
from ..upgrade_result import UpgradeResult as Result
from ..exceptions import ProtocolUpgradeError
from .protocol_upgrade_rule import ProtocolUpgradeRule, UpgradeRuleFactory
from .rule_continuum_phase_upgrade import RuleContinuumPhaseUpgrade
from .shared_rule_cache import SharedRuleCache
from .protocol_rules_cache import ProtocolRulesCache
from ..exceptions import UpgradeError


class UpgradeSummary:
    """
    Structured result of running the UpgradeEngine.
    """

    def __init__(
        self,
        artifact: FrontMatterMeta,
        errors: Dict[str, List[str]],
        warnings: Dict[str, List[str]],
        logs: List[str],
    ):
        self.artifact = artifact
        self.errors = errors
        self.warnings = warnings
        self.logs = logs

    def is_success(self) -> bool:
        return not self.errors

    def __repr__(self) -> str:
        return (
            f"UpgradeSummary(errors={self.errors}, "
            f"warnings={self.warnings}, logs={self.logs})"
        )


class UpgradeEngine:
    """
    UpgradeEngine applies ordered upgrade rules to a FrontMatter artifact.
    """

    def __init__(self):
        self._rules: Dict[str, ProtocolUpgradeRule] = {}
        self._shared_cache: ProtocolRulesCache = SharedRuleCache()
        self._register_default_rules()
        logger.debug("Initialized UpgradeEngine")

    # --------------------------
    # Registration
    # --------------------------
    def register_rule(self, rule_cls: UpgradeRuleFactory) -> None:
        instance = rule_cls(self._shared_cache)
        self._rules[instance.get_rule_id()] = instance
        logger.debug(f"Registered Upgrade Rule: {instance.get_rule_id()}")

    def unregister_rule(self, rule_id: str) -> None:
        if rule_id in self._rules:
            del self._rules[rule_id]
            logger.debug(f"Unregistered Upgrade Rule: {rule_id}")
        else:
            logger.warning(f"Tried to unregister nonexistent rule: {rule_id}")

    def unregister_all(self) -> None:
        self._rules.clear()
        logger.debug("Unregistered all upgrade rules")

    def reset(self):
        self._shared_cache.clear()
        logger.debug("Reset UpgradeEngine state and cleared shared cache")

    # --------------------------
    # Hooks (optional overrides for custom behavior)
    # --------------------------
    def before_all_rules(self):
        pass

    def after_each_rule(
        self,
        rule: ProtocolUpgradeRule,
        result: Result[FrontMatterMeta, None] | Result[None, UpgradeError],
    ):
        pass

    def after_all_rules(self, summary: UpgradeSummary):
        pass

    # --------------------------
    # Severity routing
    # --------------------------
    def _route_severity(
        self,
        rule_id: str,
        result: Result,
        errors: dict[str, Any],
        warnings: dict[str, Any],
        logs: List[str],
    ) -> bool:
        # Optional human-readable message if payload is a string
        payload_info = (
            f" payload={result.payload!r}" if result.payload is not None else ""
        )

        error = cast(ProtocolUpgradeError, result.error)
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
        fm_artifact: FrontMatterMeta,
        fm_template: FrontMatterMeta,
        registry: Dict[str, Any],
    ) -> UpgradeSummary:

        self.reset()
        self.before_all_rules()

        # Deterministic ordering based on get_order(), default = 100
        ordered_rules = sorted(
            self._rules.values(), key=lambda r: getattr(r, "get_order", lambda: 100)()
        )

        errors: Dict[str, List[str]] = {}
        warnings: Dict[str, List[str]] = {}
        logs: List[str] = []

        # Clone artifact to avoid side-effect mutation
        current_artifact = fm_artifact.copy()

        for rule in ordered_rules:
            # Rule applicability check

            should_run = rule.should_run(current_artifact, fm_template, registry)
            if not should_run:
                logs.append(f"[SKIP] Rule {rule.get_rule_id()} (should_run=False)")
                continue

            # Execute rule
            try:
                result = rule.apply(
                    fm_artifact=current_artifact,
                    fm_template=fm_template,
                    registry=registry,
                )

                if Result.is_failure(result):
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

        summary = UpgradeSummary(
            artifact=current_artifact,
            errors=errors,
            warnings=warnings,
            logs=logs,
        )

        self.after_all_rules(summary)  # Placeholder for potential future use

        return summary

    # --------------------------
    # Default rules
    # --------------------------

    def _register_default_rules(self) -> None:
        """Register the default set of processes with this processor."""
        self.register_rule(RuleContinuumPhaseUpgrade)
