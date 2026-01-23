from dataclasses import dataclass
from ..util.validation import check
from .api_info_templates import ApiInfoTemplates
from .api_env import ApiEnv


@dataclass
class ApiInfo:
    base_dir: str
    ttl_session_cache_seconds: int
    info_templates: ApiInfoTemplates
    title: str
    description: str
    version: str
    env: ApiEnv

    def __post_init__(self) -> None:
        check(self.base_dir != "", f"{self}", "base_dir cannot be empty.")
        check(
            self.ttl_session_cache_seconds > 0,
            f"{self}",
            "Value of ttl_session_cache_seconds must be greater than zero.",
        )
        check(self.title != "", f"{self}", "title cannot be empty.")
        check(self.description != "", f"{self}", "description cannot be empty.")
        check(self.version != "", f"{self}", "version cannot be empty.")
        # check that version is in semver format
        parts = self.version.split(".")
        check(
            len(parts) == 3 and all(part.isdigit() for part in parts),
            f"{self}",
            "version must be in semver format (e.g., '1.0.0').",
        )
