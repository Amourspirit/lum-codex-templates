from pydantic import BaseModel, Field


class ArgTemplateVersion(BaseModel):
    version: str = Field(
        title="Template Version",
        description="The version in the format of `vX.Y` or `X.Y`. For example, '1.0' or 'v1.0'.",
    )


class ArgTemplateVersionOptional(BaseModel):
    version: str = Field(
        default="",
        title="Template Version",
        description="The optional version of the template in the format of `vX.Y` or `X.Y`. Defaults to latest version if not provided.",
    )
