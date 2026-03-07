from typing import Any
import re
from src.template.front_mater_meta import FrontMatterMeta
from ..exceptions import UpgradeError
from ..protocols.protocol_rules_cache import ProtocolRulesCache
from ..types import PhaseInfo
from ..upgrade_result import UpgradeResult
from .rule_upgrade import RuleUpgrade


class RuleArtifactIdNormalization(RuleUpgrade[PhaseInfo]):
    RULE_ORDER = 170

    def __init__(self, shared_cache: ProtocolRulesCache[PhaseInfo]) -> None:
        super().__init__(shared_cache)
        self._rule_id = "artifact_id_normalization"
        self._description = "Ensure artifact_id is valid and normalized."

    def get_rule_id(self) -> str:
        return self._rule_id

    def get_description(self) -> str:
        return self._description

    def should_run(
        self,
        fm_artifact: FrontMatterMeta,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> bool:
        return True

    def _normalize(self, s: str) -> str:
        """
        Normalize a string by converting it to uppercase and removing invalid characters.
        This method performs the following transformations:
        1. Strips leading and trailing whitespace
        2. Converts all characters to uppercase
        3. Removes all characters except alphanumeric, underscores, and hyphens
        Args:
            s (str): The input string to normalize
        Returns:
            str: The normalized string containing only uppercase letters, digits,
                 underscores, and hyphens
        """

        s = s.strip().upper()
        return re.sub(r"[^A-Z0-9_-]", "", s)

    def apply(
        self,
        fm_artifact: FrontMatterMeta,
        fm_template: FrontMatterMeta,
        registry: dict[str, Any],
    ) -> UpgradeResult[FrontMatterMeta, None] | UpgradeResult[None, UpgradeError]:

        if not fm_artifact.has_field("artifact_id"):
            name = fm_artifact.get_field("artifact_name", "UNKNOWN")
            fm_artifact.set_field("artifact_id", self._normalize(name))

        return UpgradeResult.success(fm_artifact)
