from typing import Annotated, Optional
from pydantic import BaseModel, Field


class ArtifactSubmission(BaseModel):
    artifact_name: Annotated[
        str,
        Field(
            title="Artifact Name",
            description="Artifact name such as, `Glyph of Silent Blessing`, associated with the template to be upgraded.",
        ),
    ]
    template_content: Annotated[
        str,
        Field(
            title="Template Content",
            description="Markdown contents containing Front-matter and body associated with the artifact to be upgraded.",
        ),
    ]
