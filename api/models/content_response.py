from typing import Annotated, Optional
from pydantic import BaseModel, Field


class ContentResponse(BaseModel):
    content: Annotated[
        str,
        Field(
            description="The content formatted as Html.",
            json_schema_extra={
                "format": "html",
                "contentMediaType": "text/html",
            },  # Hint for some UI renderers
        ),
    ]

    content_media_type: Annotated[
        Optional[str],
        Field(
            default="text/html",
            description="Media type (contentMediaType) of the content, default is 'text/html'.",
        ),
    ] = "text/html"
