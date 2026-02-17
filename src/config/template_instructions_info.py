from dataclasses import dataclass
from functools import cache
from ..util.validation import check

# To cache a dataclass method in Python, you can use the @functools.cache decorator (Python 3.9+)
# or @functools.lru_cache (earlier versions).
# Note: For @cache to work with instance methods, the dataclass must be frozen (immutable) to be hashable:


@dataclass(frozen=True)
class TemplateInstructionsInfo:
    version: str

    def __post_init__(self) -> None:

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

    @cache
    def get_parsed_version(self) -> tuple[int, int, int]:
        """
        Parse the version string into its components.
        Splits the version string by dots and extracts the major, minor, and patch
        version numbers. Missing components default to 0.
        Returns:
            tuple: A tuple[int, int, int] containing (major, minor, patch) version numbers as integers.
                Each component defaults to 0 if not present in the version string.
        """

        parts = self.version.split(".")
        len_parts = len(parts)
        major = int(parts[0]) if len_parts > 0 else 0
        minor = int(parts[1]) if len_parts > 1 else 0
        patch = int(parts[2]) if len_parts > 2 else 0
        return (major, minor, patch)
