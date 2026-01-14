from pathlib import Path
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

    def _get_model(self) -> str:
        result = f"""from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field


class CbibResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Annotated[
        str,
        Field(title="ID", description="Unique identifier for the executor mode such as `CANONICAL-EXECUTOR-MODE-V{self.config.template_cbib_api.version}`."),
    ]
    name: Annotated[
        str,
        Field(title="Name", description="Name of the executor mode."),
    ]
    version: Annotated[
        str,
        Field(title="Version", description="Version of the executor mode such as `{self.config.template_cbib_api.version}`."),
    ]
    canonical_enhancements: Annotated[
        list[str],
        Field(
            title="Canonical Enhancements",
            description="List of canonical enhancements for the executor mode.",
        ),
    ]

"""
        return result

    def write_model_to_file(self) -> None:
        model_str = self._get_model()
        path = (
            self.config.root_path
            / self.config.api_info.base_dir
            / "models"
            / "executor_modes"
            / f"v{self.config.template_cbib_api.version.replace('.', '_')}"
        )
        path.mkdir(parents=True, exist_ok=True)
        file = path / "cbib_response.py"
        print(f"Writing CBIB model to {file}")
        with open(file, "w", encoding="utf-8") as f:
            f.write(model_str)
        with open(path / "__init__.py", "w", encoding="utf-8") as f:
            pass
