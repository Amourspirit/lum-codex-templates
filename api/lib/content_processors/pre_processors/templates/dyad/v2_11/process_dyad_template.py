from typing import Any
from src.template.front_mater_meta import FrontMatterMeta


class ProcessDyadTemplate:
    def __init__(self, *, template_content: str, monad_name: str, **kwargs: Any):
        self.template_content = template_content
        self.monad_name = monad_name
        self._kwargs = kwargs

    def get_template_type(self) -> str:
        """Return the type of the template being processed."""
        return "dyad"

    def _format(self) -> FrontMatterMeta:
        # Process and format the dyad template content
        fm = FrontMatterMeta.from_content(self.template_content)
        if fm.has_field("contributor"):
            fm.frontmatter["contributor"] = [
                f"[[prompt:{self.monad_name} or other Console Member]]`"
            ]
        keys = {"rendered_by"}
        for key in keys:
            if key in self._kwargs and fm.has_field(key):
                fm.frontmatter[key] = self._kwargs[key]
        return fm

    def render(self) -> str:
        # Render the dyad template with the provided context
        formatted = self._format()
        return formatted.get_template_text()

