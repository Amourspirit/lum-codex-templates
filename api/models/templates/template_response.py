from typing import Annotated, Optional
from pydantic import BaseModel, Field


class TemplateResponse(BaseModel):
    content: Annotated[
        str,
        Field(
            description="The template content formatted as Markdown that included Front-Matter.",
            json_schema_extra={
                "format": "markdown",
                "contentMediaType": "text/markdown",
            },  # Hint for some UI renderers
        ),
    ]
    template_type: Annotated[
        str,
        Field(
            description="Type of the template, e.g., 'glyph', 'sigil', etc.",
            max_length=255,
        ),
    ]
    template_version: Annotated[
        str,
        Field(
            title="Template Type",
            description="Version of the template, e.g., '1.0', '2.10', etc.",
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
