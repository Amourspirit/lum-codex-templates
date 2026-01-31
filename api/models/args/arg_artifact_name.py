from pydantic import BaseModel, Field


class ArgArtifactName(BaseModel):
    name: str = Field(
        description="The name of the artifact such as 'Glyph of <artifact>'."
    )
