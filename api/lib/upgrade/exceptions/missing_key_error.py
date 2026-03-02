from .protocol_upgrade_error import ProtocolUpgradeError
from .upgrade_error import UpgradeError


class MissingKeyError(UpgradeError, ProtocolUpgradeError):
    """Custom exception for missing key errors."""

    pass
