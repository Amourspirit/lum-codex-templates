from typing import Protocol
from pathlib import Path


class ProtocolTemplatePreProcessor(Protocol):
    def get_template_type(self) -> str: ...
    def write_file(self, pre_processor_dir: Path) -> Path: ...
