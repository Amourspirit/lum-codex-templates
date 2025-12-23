from dataclasses import dataclass, field
from ..util.validation import check


@dataclass
class TemplateCeibInfo:
    executor_mode: str
    title: str
    version: str

    def __post_init__(self) -> None:
        check(
            self.executor_mode != "",
            f"{self}",
            "Value of id must not be empty.",
        )
        # self.id must contain only alphanumeric characters, hyphens, and underscores
        check(
            all(c.isalnum() or c in "-_" for c in self.executor_mode),
            f"{self}",
            "Value of id must contain only alphanumeric characters, hyphens, and underscores.",
        )
        check(
            self.title != "",
            f"{self}",
            "Value of title must not be empty.",
        )

        check(
            self.version != "",
            f"{self}",
            "Value of version must not be empty.",
        )
        # version should follow semantic versioning format: MAJOR.MINOR or MAJOR.MINOR.PATCH
        parts = self.version.split(".")
        check(
            len(parts) in (2, 3) and all(part.isdigit() for part in parts),
            f"{self}",
            "Value of version must follow semantic versioning format: MAJOR.MINOR or MAJOR.MINOR.PATCH.",
        )
