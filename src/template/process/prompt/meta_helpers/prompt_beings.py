from dataclasses import dataclass, field
from typing import Dict, List
from pathlib import Path
import yaml


@dataclass
class BeingEntry:
    role_title: str
    template_types_governed: List[str] = field(default_factory=list)

    def validate(self) -> None:
        if not isinstance(self.role_title, str) or not self.role_title:
            raise ValueError("role_title must be a non-empty string")
        if not isinstance(self.template_types_governed, list):
            raise TypeError("template_types_governed must be a list")
        if not all(isinstance(t, str) and t for t in self.template_types_governed):
            raise ValueError(
                "All items in template_types_governed must be non-empty strings"
            )


@dataclass
class PromptBeings:
    beings: Dict[str, BeingEntry] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path | str) -> "PromptBeings":
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"{p} not found")
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        raw = data.get("beings", {})
        if not isinstance(raw, dict):
            raise TypeError("`beings` must be a mapping in the YAML")

        parsed: Dict[str, BeingEntry] = {}
        for name, entry in raw.items():
            if not isinstance(entry, dict):
                raise TypeError(f"`beings.{name}` must be a mapping")
            be = BeingEntry(
                role_title=str(entry.get("role_title", "") or ""),
                template_types_governed=list(
                    entry.get("template_types_governed") or []
                ),
            )
            be.validate()
            parsed[name] = be

        return cls(beings=parsed)
