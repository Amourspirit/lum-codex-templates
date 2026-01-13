from pydantic import BaseModel, Field
from typing import Annotated, Optional


class UserResponse(BaseModel):
    username: Annotated[
        str, Field(title="Username", description="The user's username.")
    ]
    name: Annotated[str, Field(title="Name", description="The user's name.")]
    email: Annotated[str, Field(title="Email", description="The user's email address.")]
    roles: Annotated[
        list[str],
        Field(title="Roles", description="List of roles assigned to the user."),
    ]
    is_active: Annotated[
        bool,
        Field(title="Active Status", description="Indicates if the user is active."),
    ]
    monad_name: Annotated[
        Optional[str], Field(title="Monad Name", description="The user's monad name.")
    ] = None

    class Config:
        from_attributes = True
