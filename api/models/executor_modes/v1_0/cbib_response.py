from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field


class CbibResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Annotated[
        str,
        Field(title="ID", description="Unique identifier for the executor mode such as `CANONICAL-EXECUTOR-MODE-V1.0`."),
    ]
    name: Annotated[
        str,
        Field(title="Name", description="Name of the executor mode."),
    ]
    version: Annotated[
        str,
        Field(title="Version", description="Version of the executor mode such as `1.0`."),
    ]
    canonical_enhancements: Annotated[
        list[str],
        Field(
            title="Canonical Enhancements",
            description="List of canonical enhancements for the executor mode.",
        ),
    ]

