from typing import Any
from typing import Protocol
from pathlib import Path
from ....main_registry import MainRegistry
from ....front_mater_meta import FrontMatterMeta


class ProtocolTemplateReg(Protocol):
    def __init__(
        self,
        main_registry: MainRegistry,
        templates_meta: dict[str, dict[str, Any]],
        templates_data: dict[str, FrontMatterMeta],
    ): ...

    def process(self, tokens: dict[str, Any]) -> tuple[str, Path]: ...
