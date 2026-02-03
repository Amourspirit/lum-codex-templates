from typing import Annotated
from pydantic import BaseModel, Field


class UpgradeToTemplateSubmission(BaseModel):
    artifact_name: Annotated[
        str,
        Field(
            title="Artifact Name",
            description="Artifact name such as, `Glyph of Silent Blessing`, associated with the template to be upgraded.",
        ),
    ]
    markdown_content: Annotated[
        str,
        Field(
            title="Markdown Content",
            description="Content of the markdown template containing Front-matter and body associated with the artifact to be upgraded.",
            json_schema_extra={"format": "textarea"},
        ),
    ]
    new_version: Annotated[
        str,
        Field(
            default="",
            title="New version",
            description="The optional new version that the template should be upgraded to, e.g., '1.0', '2.10', etc. Defaults to 'latest' if not provided.",
        ),
    ]
