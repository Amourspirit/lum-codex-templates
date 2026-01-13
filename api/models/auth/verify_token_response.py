from typing import Annotated
from pydantic import BaseModel, Field


class VerifyTokenResponse(BaseModel):
    valid: Annotated[
        bool, Field(title="Valid", description="Indicates if the token is valid.")
    ]
    username: Annotated[
        str, Field(title="Username", description="The user's username.")
    ]
    name: Annotated[str, Field(title="Name", description="The user's name.")]
    email: Annotated[str, Field(title="Email", description="The user's email address.")]
    roles: Annotated[
        list[str],
        Field(title="Roles", description="List of roles assigned to the user."),
    ]
