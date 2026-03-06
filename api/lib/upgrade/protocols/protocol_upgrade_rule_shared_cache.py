from typing import Generic, Protocol, TypeVar, runtime_checkable
from .protocol_upgrade_rule import ProtocolUpgradeRule
from .protocol_shared_cache import ProtocolSharedCache
from .protocol_rules_cache import ProtocolRulesCache

C = TypeVar("C")  # Cache type variable


@runtime_checkable
class ProtocolUpgradeRuleSharedCache(
    ProtocolUpgradeRule, ProtocolSharedCache[C], Generic[C]
):
    pass


class UpgradeRuleSharedCacheFactory(Protocol, Generic[C]):
    """Protocol for class constructors."""

    def __call__(
        self, shared_cache: ProtocolRulesCache[C]
    ) -> ProtocolUpgradeRuleSharedCache[C]: ...
