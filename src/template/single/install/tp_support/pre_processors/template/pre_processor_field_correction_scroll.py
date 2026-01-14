from .protocol_template_pre_processor import ProtocolTemplatePreProcessor
from .template_base_pre_processor import TemplateBasePreProcessor


class PreProcessorFieldCorrectionScroll(
    TemplateBasePreProcessor, ProtocolTemplatePreProcessor
):
    def __init__(self) -> None:
        super().__init__()

    def get_template_type(self) -> str:
        """Return the type of the template being processed."""
        return "field_correction_scroll"

    def _get_file_name(self) -> str:
        return "process_field_correction_scroll_template.py"

    def _get_content(self) -> str:
        return """from typing import Any
from src.template.front_mater_meta import FrontMatterMeta


class ProcessFieldCorrectionScrollTemplate:
    def __init__(self, *, template_content: str, monad_name: str, **kwargs: Any):
        self.template_content = template_content
        self.monad_name = monad_name
        self._kwargs = kwargs

    def get_template_type(self) -> str:
        \"\"\"Return the type of the template being processed.\"\"\"
        return "field_correction_scroll"

    def _format(self) -> FrontMatterMeta:
        # Process and format the field_correction_scroll template content
        fm = FrontMatterMeta.from_content(self.template_content)
        return fm

    def render(self) -> str:
        # Render the field_correction_scroll template with the provided context
        formatted = self._format()
        return formatted.get_template_text()

"""
