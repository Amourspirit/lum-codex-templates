from typing import Annotated
from pydantic import BaseModel, Field


class HashedPasswordResponse(BaseModel):
    hashed_password: Annotated[
        str,
        Field(
            title="Hashed Password",
            description="The hashed version of the provided plain text password.",
        ),
    ]
