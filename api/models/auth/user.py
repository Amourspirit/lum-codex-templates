from typing import Optional, Annotated
from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    model_config = ConfigDict(extra="allow")
    username: Annotated[
        str, Field(title="Username", description="The user's username.")
    ]
    name: Annotated[str, Field(title="Name", description="The user's name.")]
    email: Annotated[str, Field(title="Email", description="The user's email address.")]
    roles: Annotated[
        list[str],
        Field(title="Roles", description="List of roles assigned to the user."),
    ]
    hashed_pwd: Annotated[
        str, Field(title="Hashed Password", description="The user's hashed password.")
    ]
    is_active: Annotated[
        bool,
        Field(title="Active Status", description="Indicates if the user is active."),
    ]
    monad_name: Annotated[
        Optional[str], Field(title="Monad Name", description="The user's monad name.")
    ] = None
