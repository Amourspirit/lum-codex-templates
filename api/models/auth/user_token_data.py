from pydantic import BaseModel, Field
from typing import Annotated, Optional


class TokenData(BaseModel):
    username: Annotated[
        Optional[str], Field(title="Username", description="The user's username.")
    ] = None
