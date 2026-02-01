import json
from pathlib import Path
from typing import Annotated
from dataclasses import dataclass


@dataclass
class TemplateEntry:
    name: Annotated[str, "The name of the template."]
    type: Annotated[str, "The type of the template such as 'glyph', 'dyad', etc."]
    versions: Annotated[
        list[str],
        "List of available versions for the template. Each version is a string in the format 'major.minor.patch' or `major.minor`",
    ]

    def __post_init__(self) -> None:
        if not isinstance(self.versions, list):
            raise TypeError("versions must be a list of strings")
        for v in self.versions:
            if not isinstance(v, str):
                raise TypeError("each version must be a string")
        # Validate version format
        for v in self.versions:
            parts = v.split(".")
            if len(parts) < 2 or len(parts) > 3:
                raise ValueError(
                    f"Invalid version format: {v}. Expected 'major.minor' or 'major.minor.patch'."
                )
            for part in parts:
                if not part.isdigit():
                    raise ValueError(
                        f"Invalid version part: {part} in version {v}. Must be an integer."
                    )
        # Remove duplicate versions while preserving order
        seen = set()
        unique_versions = []
        for v in self.versions:
            if v not in seen:
                seen.add(v)
                unique_versions.append(v)
        object.__setattr__(self, "versions", unique_versions)


@dataclass
class TemplatesManifest:
    templates: dict[str, TemplateEntry]
    """Dictionary mapping template type to their entries."""

    def get_sorted_templates(self) -> "TemplatesManifest":
        """Return the templates sorted by their names and versions."""
        sorted_templates: dict[str, TemplateEntry] = {}
        for key, entry in sorted(self.templates.items(), key=lambda x: x[1].name):
            # Sort versions descending (highest first) by parsing as semantic version
            sorted_versions = sorted(
                entry.versions,
                key=lambda v: [int(x) for x in v.split(".")],
                reverse=True,
            )
            sorted_templates[key] = TemplateEntry(
                name=entry.name, type=entry.type, versions=sorted_versions
            )
        return TemplatesManifest(templates=sorted_templates)

    @staticmethod
    def from_json_file(path: str | Path) -> "TemplatesManifest":
        """Load the templates manifest from a JSON file."""
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"Templates manifest file not found: {p}")

        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        templates_dict = {
            key: TemplateEntry(
                name=value["name"],
                type=value["type"],
                versions=value["versions"],
            )
            for key, value in data["templates"].items()
        }
        return TemplatesManifest(templates=templates_dict)
