from typing import Any
from typing import Protocol
from pathlib import Path
from ....main_registry import MainRegistry
from ....front_mater_meta import FrontMatterMeta


class ProtocolEnforcement(Protocol):
    def __init__(
        self,
        working_dir: Path,
        main_registry: MainRegistry,
        templates_data: dict[str, FrontMatterMeta],
    ): ...

    def process(self, tokens: dict[str, Any]) -> Path: ...
