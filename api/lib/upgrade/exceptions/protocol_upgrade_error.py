from typing import Protocol


class ProtocolUpgradeError(Protocol):
    message: str
    field_name: str
    errors: list[str]
