from pydantic import BaseModel


# Artifact submission model (simplified)
class ArtifactSubmission(BaseModel):
    template_frontmatter: str
    template_body: str
