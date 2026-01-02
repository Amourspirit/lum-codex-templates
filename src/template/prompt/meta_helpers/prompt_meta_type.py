from dataclasses import dataclass, field
from typing import Dict, List, Any
from pathlib import Path
import yaml


@dataclass
class TemplateEntryCreate:
    invocation: str


@dataclass
class TemplateEntry:
    autofill_enabled: bool
    beings: List[str] = field(default_factory=list)
    default_field_being: str = ""
    role: str = ""
    invocation: str = ""
    invocation_agents: Dict[str, str] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    create: TemplateEntryCreate | None = None

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not isinstance(self.autofill_enabled, bool):
            raise TypeError("autofill_enabled must be a bool")
        if not isinstance(self.beings, list) or not all(
            isinstance(b, str) and b for b in self.beings
        ):
            raise ValueError("beings must be a non-empty list of strings")
        if (
            not isinstance(self.default_field_being, str)
            or not self.default_field_being
        ):
            raise ValueError("default_field_being must be a non-empty string")
        if not isinstance(self.role, str) or not self.role:
            raise ValueError("role must be a non-empty string")
        if not isinstance(self.invocation, str) or not self.invocation:
            raise ValueError("invocation must be a non-empty string")
        if not isinstance(self.invocation_agents, dict):
            raise TypeError("invocation_agents must be a mapping of strings")
        if not isinstance(self.tags, list) or not all(
            isinstance(t, str) for t in self.tags
        ):
            raise TypeError("tags must be a list of strings")

    def has_create(self) -> bool:
        """Check if the create entry is defined."""
        return self.create is not None


@dataclass
class PromptMetaType:
    template_type: Dict[str, TemplateEntry] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path | str) -> "PromptMetaType":
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"{p} not found")
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        tt = data.get("template_type", {})
        if not isinstance(tt, dict):
            raise TypeError("template_type must be a table/dictionary in the YAML")

        parsed: Dict[str, TemplateEntry] = {}
        for name, entry in tt.items():
            if not isinstance(entry, dict):
                raise TypeError(f"template_type.{name} must be a mapping")

            create_entry = entry.get("create")
            create_obj = None
            if create_entry is not None:
                if not isinstance(create_entry, dict):
                    raise TypeError(f"template_type.{name}.create must be a mapping")
                create_obj = TemplateEntryCreate(
                    invocation=str(create_entry.get("invocation", "") or "")
                )

            te = TemplateEntry(
                autofill_enabled=bool(entry.get("autofill_enabled", False)),
                beings=list(entry.get("beings") or []),
                default_field_being=str(entry.get("default_field_being", "") or ""),
                role=str(entry.get("role", "") or ""),
                invocation=str(entry.get("invocation", "") or ""),
                invocation_agents=dict(entry.get("invocation_agents") or {}),
                tags=list(entry.get("tags") or []),
                create=create_obj,
            )
            parsed[name] = te

        return cls(template_type=parsed)
