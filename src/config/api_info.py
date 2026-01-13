from dataclasses import dataclass, field
from ..util.validation import check
from .api_info_templates import ApiInfoTemplates


@dataclass
class ApiInfo:
    base_dir: str
    ttl_session_cache_seconds: int
    info_templates: ApiInfoTemplates

    def __post_init__(self) -> None:
        check(self.base_dir != "", f"{self}", "base_dir cannot be empty.")
        check(
            self.ttl_session_cache_seconds > 0,
            f"{self}",
            "Value of ttl_session_cache_seconds must be greater than zero.",
        )
