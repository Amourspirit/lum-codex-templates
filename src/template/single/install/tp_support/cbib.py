from typing import Any
from .....config.pkg_config import PkgConfig


class CBIB:
    def __init__(self) -> None:
        self.config = PkgConfig()

    def get_cbib(self) -> dict[str, Any]:
        results = {
            "id": f"CANONICAL-EXECUTOR-MODE-V{self.config.template_cbib_api.version}",
            "name": "Codex Bootstrap Instruction Bundle",
            "version": self.config.template_cbib_api.version,
            "canonical_enhancements": [
                "Canonical abort payload specification",
                "Mandatory pre-flight validation phase",
                "Explicit STRICT MODE prohibitions",
                "Explicit template_type & template_family enforcement",
                "Structured directive grouping",
                "Hard rendering gate (no partial output)",
                "Zero tolerance for unresolved prompts or conditionals",
                "Template lifecycle status checks",
                "Cross-template contamination prevention",
                "Template output mode validation",
            ],
        }
        return results
