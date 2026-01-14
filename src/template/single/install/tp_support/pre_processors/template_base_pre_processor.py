from abc import abstractmethod
from pathlib import Path


class TemplateBasePreProcessor:
    def __init__(self) -> None:
        pass

    def write_file(self, pre_processor_dir: Path) -> Path:
        if not pre_processor_dir.exists():
            pre_processor_dir.mkdir(parents=True, exist_ok=True)
        file_name = self._get_file_name()
        full_path = pre_processor_dir / file_name
        content = self._get_content()
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return full_path

    @abstractmethod
    def get_template_type(self) -> str:
        pass

    @abstractmethod
    def _get_file_name(self) -> str:
        pass

    @abstractmethod
    def _get_content(self) -> str:
        pass
