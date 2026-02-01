from typing import Annotated
from pydantic import BaseModel, Field


class TemplateEntry(BaseModel):
    type: Annotated[
        str,
        "The type of the template such as 'glyph', 'dyad', etc.",
    ]
    versions: Annotated[
        list[str],
        Field(
            title="Versions",
            description="List of available versions for the template. Each version is a string in the format 'major.minor.patch' or `major.minor`",
            default_factory=list,
        ),
    ]


class TemplatesVersions(BaseModel):
    templates: Annotated[
        dict[str, TemplateEntry],
        Field(
            title="Templates",
            description="Dictionary mapping template type to their entries.",
            default_factory=dict,
        ),
    ]

    def get_sorted_templates(self) -> "TemplatesVersions":
        """Return the templates sorted by their names and versions."""
        sorted_templates: dict[str, TemplateEntry] = {}
        for key, entry in sorted(self.templates.items(), key=lambda x: x[1].type):
            # Sort versions descending (highest first) by parsing as semantic version
            sorted_versions = sorted(
                entry.versions,
                key=lambda v: [int(x) for x in v.split(".")],
                reverse=True,
            )
            sorted_templates[key] = TemplateEntry(
                type=entry.type, versions=sorted_versions
            )
        return TemplatesVersions(templates=sorted_templates)

    def add_entry(self, template_key: str, type: str, versions: list[str]) -> None:
        """Add a new template entry to the templates dictionary."""
        self.templates[template_key] = TemplateEntry(
            type=type,
            versions=versions,
        )
