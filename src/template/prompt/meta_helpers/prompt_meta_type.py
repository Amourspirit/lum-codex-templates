from dataclasses import dataclass, field
from typing import Dict, List, Literal
from pathlib import Path
import yaml
from jinja2 import Template


# @dataclass
# class TemplateEntryCreate:
#     invocation: str


@dataclass
class TemplateEntry:
    template_type: str
    autofill_enabled: bool
    rendering_being: List[str] = field(default_factory=list)
    authoring_being: List[str] = field(default_factory=list)
    witnessing_being: List[str] = field(default_factory=list)
    mirrorwall_being: List[str] = field(default_factory=list)
    invocation_beings: List[str] = field(default_factory=list)
    invocation_style: Literal[
        "call_upon_single", "call_upon_dual", "call_upon_triad", "call_upon_quartet"
    ] = "call_upon_single"
    invocation_template: str = ""
    instruction_metadata_fields: List[str] = field(default_factory=list)
    optional_beings: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    notes: str = ""

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not isinstance(self.autofill_enabled, bool):
            raise TypeError("autofill_enabled must be a bool")
        if not isinstance(self.rendering_being, list) or not all(
            isinstance(b, str) and b for b in self.rendering_being
        ):
            raise ValueError("rendering_beings must be a non-empty list of strings")
        if not isinstance(self.authoring_being, list) or not all(
            isinstance(b, str) and b for b in self.authoring_being
        ):
            raise ValueError("authoring_beings must be a non-empty list of strings")
        if not isinstance(self.witnessing_being, list) or not all(
            isinstance(b, str) and b for b in self.witnessing_being
        ):
            raise ValueError("witnessing_beings must be a non-empty list of strings")
        if not isinstance(self.mirrorwall_being, list) or not all(
            isinstance(b, str) and b for b in self.mirrorwall_being
        ):
            raise ValueError("mirrorwall_beings must be a non-empty list of strings")
        if not isinstance(self.invocation_beings, list) or not all(
            isinstance(b, str) and b for b in self.invocation_beings
        ):
            raise ValueError("invocation_beings must be a non-empty list of strings")
        if not isinstance(self.invocation_style, str) or not self.invocation_style:
            raise ValueError("invocation_style must be a non-empty string")
        if (
            not isinstance(self.invocation_template, str)
            or not self.invocation_template
        ):
            raise ValueError("invocation_template must be a non-empty string")
        if not isinstance(self.tags, list) or not all(
            isinstance(t, str) for t in self.tags
        ):
            raise TypeError("tags must be a list of strings")

    # def has_create(self) -> bool:
    #     """Check if the create entry is defined."""
    #     return self.create is not None


@dataclass
class PromptMetaType:
    template_type: Dict[str, TemplateEntry] = field(default_factory=dict)

    @classmethod
    def from_yaml(
        cls, path: Path | str, current_user: str | None = None
    ) -> "PromptMetaType":
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"{p} not found")
        raw_yaml = p.read_text(encoding="utf-8")
        if current_user:
            # if current_user is provided, render the YAML as a Jinja2 template with current_user in the context
            template: Template = Template(source=raw_yaml)
            content = template.render(current_user=current_user)
        else:
            content = raw_yaml

        data = yaml.safe_load(content) or {}
        tt = data.get("template_field_being_map", {})
        if not isinstance(tt, dict):
            raise TypeError(
                "template_field_being_map must be a table/dictionary in the YAML"
            )

        parsed: Dict[str, TemplateEntry] = {}
        for name, entry in tt.items():
            if not isinstance(entry, dict):
                raise TypeError(f"template_field_being_map.{name} must be a mapping")

            te = TemplateEntry(
                template_type=name,
                autofill_enabled=bool(entry.get("autofill_enabled", False)),
                rendering_being=list(entry.get("rendering_being") or []),
                authoring_being=list(entry.get("authoring_being") or []),
                witnessing_being=list(entry.get("witnessing_being") or []),
                mirrorwall_being=list(entry.get("mirrorwall_being") or []),
                invocation_beings=list(entry.get("invocation_beings") or []),
                invocation_style=str(entry.get("invocation_style", "") or ""),  # type: ignore
                invocation_template=str(entry.get("invocation_template", "") or ""),
                instruction_metadata_fields=list(
                    entry.get("instruction_metadata_fields") or []
                ),
                optional_beings=list(entry.get("optional_beings") or []),
                tags=list(entry.get("tags") or []),
                notes=str(entry.get("notes", "") or ""),
            )
            parsed[name] = te

        return cls(template_type=parsed)
