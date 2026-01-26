from typing import Annotated, Optional
from pydantic import BaseModel, Field


class HtmlResponse(BaseModel):
    content: Annotated[
        str,
        Field(
            description="The template content formatted as HTML.",
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
