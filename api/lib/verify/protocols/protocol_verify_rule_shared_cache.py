from typing import Generic, Protocol, TypeVar, runtime_checkable
from .protocol_verify_rule import ProtocolVerifyRule
from api.lib.protocols import ProtocolSharedCache
from api.lib.protocols import ProtocolRulesCache

C = TypeVar("C")  # Cache type variable


@runtime_checkable
class ProtocolVerifyRuleSharedCache(
    ProtocolVerifyRule, ProtocolSharedCache[C], Generic[C]
):
    pass


class VerifyRuleSharedCacheFactory(Protocol, Generic[C]):
    """Protocol for class constructors."""

    def __call__(
        self, shared_cache: ProtocolRulesCache[C]
    ) -> ProtocolVerifyRuleSharedCache[C]: ...
