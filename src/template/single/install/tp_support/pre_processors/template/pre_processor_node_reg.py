from .protocol_template_pre_processor import ProtocolTemplatePreProcessor
from .template_base_pre_processor import TemplateBasePreProcessor


class PreProcessorNodeReg(TemplateBasePreProcessor, ProtocolTemplatePreProcessor):
    def __init__(self) -> None:
        super().__init__()

    def get_template_type(self) -> str:
        """Return the type of the template being processed."""
        return "node_reg"

    def _get_file_name(self) -> str:
        return "process_node_reg_template.py"

    def _get_content(self) -> str:
        return """from typing import Any
from src.template.front_mater_meta import FrontMatterMeta


class ProcessNodeRegTemplate:
    def __init__(self, *, template_content: str, monad_name: str, **kwargs: Any):
        self.template_content = template_content
        self.monad_name = monad_name
        self._kwargs = kwargs

    def get_template_type(self) -> str:
        \"\"\"Return the type of the template being processed.\"\"\"
        return "node_reg"

    def _format(self) -> FrontMatterMeta:
        # Process and format the node_reg template content
        fm = FrontMatterMeta.from_content(self.template_content)
        if fm.has_field("glyph_activator"):
            fm.frontmatter["glyph_activator"] = [self.monad_name]
        # keys = {"source_medium"}
        # for key in keys:
        #     if key in self._kwargs and fm.has_field(key):
        #         fm.frontmatter[key] = self._kwargs[key]
        return fm

    def render(self) -> str:
        # Render the node_reg template with the provided context
        formatted = self._format()
        return formatted.get_template_text()

"""
