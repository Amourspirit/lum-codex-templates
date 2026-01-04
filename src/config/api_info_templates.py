from dataclasses import dataclass
from ..util.validation import check


@dataclass
class ApiInfoTemplates:
    dir_name: str

    def __post_init__(self) -> None:
        check(
            self.dir_name != "",
            f"{self}",
            "Value of dir_name must not be empty.",
        )
        # self.dir_name must contain only alphanumeric characters, hyphens, and underscores
        check(
            all(c.isalnum() or c in "-_" for c in self.dir_name),
            f"{self}",
            "Value of dir_name must contain only alphanumeric characters, hyphens, and underscores.",
        )
