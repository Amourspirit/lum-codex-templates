from __future__ import annotations
from typing import Any, List, Dict, cast
from loguru import logger

from src.template.front_mater_meta import FrontMatterMeta
from .protocol_upgrade_rule import ProtocolUpgradeRule
from ..exceptions import ProtocolUpgradeError
from src.util.result import Result, SeverityKind


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
        logger.debug("Initialized UpgradeEngine")

    # --------------------------
    # Registration API
    # --------------------------
    def register_rule(self, rule: ProtocolUpgradeRule) -> None:
        self._rules[rule.get_rule_id()] = rule
        logger.debug(f"Registered Upgrade Rule: {rule.get_rule_id()}")

    def unregister_rule(self, rule_id: str) -> None:
        if rule_id in self._rules:
            del self._rules[rule_id]
            logger.debug(f"Unregistered Upgrade Rule: {rule_id}")
        else:
            logger.warning(f"Tried to unregister nonexistent rule: {rule_id}")

    def unregister_all(self) -> None:
        self._rules.clear()
        logger.debug("Unregistered all upgrade rules")

    # --------------------------
    # Core Execution
    # --------------------------
    def _route_severity(
        self,
        rule_id: str,
        result: Result,
        errors: dict[str, Any],
        warnings: dict[str, Any],
    ) -> None:
        sev = result.severity or SeverityKind.ERROR
        error = cast(ProtocolUpgradeError, result.error)
        if sev == SeverityKind.WARNING:
            warnings.setdefault(rule_id, []).extend(error.errors)
        else:
            errors.setdefault(rule_id, []).extend(error.errors)

    def apply(
        self,
        fm_artifact: FrontMatterMeta,
        fm_template: FrontMatterMeta,
        registry: Dict[str, Any],
    ) -> UpgradeSummary:

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
                    self._route_severity(rule.get_rule_id(), result, errors, warnings)
                else:
                    # Rule succeeded — update artifact reference
                    current_artifact = result.data
                    logs.append(f"[OK] Rule {rule.get_rule_id()} applied successfully")

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

        return summary
