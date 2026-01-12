from typing import Annotated, Optional
from pydantic import BaseModel, Field
from datetime import datetime as dt_now


class TemplateStatusResponse(BaseModel):
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
    last_verified: dt_now
    status: Annotated[
        Optional[str],
        Field(
            default="available",
            title="Status",
            description="Template Status: `verified`, 'available' or 'unavailable'.",
        ),
    ] = "available"
    template: Annotated[
        Optional[str],
        Field(
            default="available",
            title="Template",
            description="Template: 'available' or 'unavailable'.",
        ),
    ] = "available"
    registry: Annotated[
        Optional[str],
        Field(
            default="available",
            title="Registry",
            description="Registry: 'available' or 'unavailable'.",
        ),
    ] = "available"
    manifest: Annotated[
        Optional[str],
        Field(
            default="available",
            title="Manifest",
            description="Manifest: 'available' or 'unavailable'.",
        ),
    ] = "available"
    instructions: Annotated[
        Optional[str],
        Field(
            default="available",
            title="Instructions",
            description="Instructions: 'available' or 'unavailable'.",
        ),
    ] = "available"
