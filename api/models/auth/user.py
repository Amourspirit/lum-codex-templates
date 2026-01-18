from typing import Optional, Annotated
from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    model_config = ConfigDict(extra="allow")
    monad_name: Annotated[
        Optional[str], Field(title="Monad Name", description="The user's monad name.")
    ] = None
