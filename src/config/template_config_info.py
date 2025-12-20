from dataclasses import dataclass, field
from ..util.validation import check


@dataclass
class TemplateConfigInfo:
    template_id: str
    template_name: str
    template_category: str
    template_version: str
    template_family: str
    template_type: str
    single_fields_omitted: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        check(
            self.template_id != "",
            f"{self}",
            "Value of template_id must not be empty.",
        )
        # self.template_id must contain only alphanumeric characters, hyphens, and underscores
        check(
            all(c.isalnum() or c in "-_" for c in self.template_id),
            f"{self}",
            "Value of template_id must contain only alphanumeric characters, hyphens, and underscores.",
        )
        check(
            self.template_name != "",
            f"{self}",
            "Value of template_name must not be empty.",
        )
        check(
            self.template_category != "",
            f"{self}",
            "Value of template_category must not be empty.",
        )
        check(
            self.template_version != "",
            f"{self}",
            "Value of template_version must not be empty.",
        )
        # template_version should follow semantic versioning format: MAJOR.MINOR or MAJOR.MINOR.PATCH
        parts = self.template_version.split(".")
        check(
            len(parts) in (2, 3) and all(part.isdigit() for part in parts),
            f"{self}",
            "Value of template_version must follow semantic versioning format: MAJOR.MINOR or MAJOR.MINOR.PATCH.",
        )
        check(
            self.template_family != "",
            f"{self}",
            "Value of template_family must not be empty.",
        )
        # self.template_family must contain only alphanumeric characters, and underscores
        check(
            all(c.isalnum() or c == "_" for c in self.template_family),
            f"{self}",
            "Value of template_family must contain only alphanumeric characters and underscores.",
        )
        check(
            self.template_type != "",
            f"{self}",
            "Value of template_type must not be empty.",
        )
        # self.template_type must contain only alphanumeric characters, hyphens, and underscores
        check(
            all(c.isalnum() or c in "-_" for c in self.template_type),
            f"{self}",
            "Value of template_type must contain only alphanumeric characters, hyphens, and underscores.",
        )
