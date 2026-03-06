from dataclasses import dataclass
from ..util.validation import check


@dataclass
class TemplateSingleInfo:
    prompt_metadata_fields: list[str]

    def __post_init__(self) -> None:
        check(
            isinstance(self.prompt_metadata_fields, list),
            f"{self}",
            "Value of prompt_metadata_fields must be a list of strings.",
        )
        for meta_field in self.prompt_metadata_fields:
            check(
                isinstance(meta_field, str),
                f"{self}",
                "Each item in prompt_metadata_fields must be a string.",
            )
