from dataclasses import dataclass, field
from ..util.validation import check


@dataclass
class TemplateCbibInfo:
    id: str
    title: str
    version: str
    cbib_type: str

    def __post_init__(self) -> None:
        check(
            self.id != "",
            f"{self}",
            "Value of id must not be empty.",
        )
        # self.id must contain only alphanumeric characters, hyphens, and underscores
        check(
            all(c.isalnum() or c in "-_" for c in self.id),
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
        check(
            self.cbib_type != "",
            f"{self.cbib_type}",
            "Value of id must not be empty.",
        )
        # cbib_type must contain only alphanumeric characters, hyphens, and underscores
        check(
            all(c.isalnum() or c in "-_" for c in self.cbib_type),
            f"{self.cbib_type}",
            "Value of cbib_type must contain only alphanumeric characters, hyphens, and underscores.",
        )
