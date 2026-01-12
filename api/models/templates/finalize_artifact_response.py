from typing import Annotated
from pydantic import BaseModel, Field


class FinalizeArtifactResponse(BaseModel):
    status: Annotated[
        int,
        Field(
            default=200,
            title="Status",
            description="Http Status Code: 200 for finalized, or 422 for failed.",
        ),
    ] = 200
    template_content: Annotated[
        str,
        Field(
            title="Template Content",
            description="Content of the finalized template.",
        ),
    ]
