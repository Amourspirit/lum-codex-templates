from pydantic import BaseModel, Field


class ArgArtifactName(BaseModel):
    name: str = Field(
        description="The name of the artifact such as 'Glyph of <artifact>'."
    )


class ArgArtifactNameOptional(BaseModel):
    name: str = Field(
        default="",
        description="The optional name of the artifact such as 'Glyph of <artifact>'.",
    )
