from dataclasses import dataclass, field
from ..util.validation import check
from .api_info_templates import ApiInfoTemplates


@dataclass
class ApiInfo:
    base_dir: str
    info_templates: ApiInfoTemplates

    def __post_init__(self) -> None:
        check(
            self.base_dir != "",
            f"{self}",
            "Value of base_dir must not be empty.",
        )
        # self.base_dir must contain only alphanumeric characters, hyphens, and underscores
        check(
            all(c.isalnum() or c in "-_" for c in self.base_dir),
            f"{self}",
            "Value of base_dir must contain only alphanumeric characters, hyphens, and underscores.",
        )
