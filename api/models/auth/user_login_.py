from typing import Annotated
from pydantic import BaseModel, Field


class UserLogin(BaseModel):
    email: Annotated[str, Field(title="Email", description="The user's email address.")]
    password: Annotated[
        str,
        Field(title="Password", description="The user's plain text password."),
    ]
