from pydantic import BaseModel, Field


class ArgTemplateType(BaseModel):
    type: str = Field(
        description="The type of the template (e.g., 'glyph', 'stone', 'dyad', 'node_reg', etc.)."
    )
