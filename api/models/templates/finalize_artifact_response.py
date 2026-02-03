from typing import Annotated, Optional
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
    content: Annotated[
        str,
        Field(
            title="Template Content",
            description="Content of the finalized template.",
        ),
    ]
    content_media_type: Annotated[
        Optional[str],
        Field(
            default="text/markdown",
            description="Media type (contentMediaType) of the content, default is 'text/markdown'.",
        ),
    ] = "text/markdown"
    content_has_front_matter: Annotated[
        Optional[bool],
        Field(
            default=True,
            description="Indicates if the content includes Front-Matter, default is True.",
        ),
    ] = True
