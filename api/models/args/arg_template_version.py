from pydantic import BaseModel, Field


class ArgTemplateVersion(BaseModel):
    version: str = Field(
        description="The version of the executor mode in the format of `vX.Y` or `X.Y`. For example, '1.0' or 'v1.0'."
    )
