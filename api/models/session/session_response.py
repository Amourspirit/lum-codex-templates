from typing import Annotated
from pydantic import BaseModel, Field


class SessionResponse(BaseModel):
    session_id: Annotated[
        str,
        Field(title="Session ID", description="The unique identifier for the session."),
    ]
    new_session: Annotated[
        bool,
        Field(
            title="New Session", description="Indicates if a new session was created."
        ),
    ]
    message: Annotated[
        str,
        Field(title="Message", description="A message related to the session."),
    ]
    expires_in_seconds: Annotated[
        int,
        Field(
            title="Expires In Seconds",
            description="Time in seconds until the session expires.",
        ),
    ]
