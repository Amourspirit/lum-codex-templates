from typing import Annotated
from pydantic import BaseModel, Field


class Session(BaseModel):
    session_id: Annotated[
        str,
        Field(title="Session ID", description="The unique identifier for the session."),
    ]
    started_at: Annotated[
        str,
        Field(
            title="Started At",
            description="Timestamp indicating when the session started.",
        ),
    ]
    last_accessed: Annotated[
        str,
        Field(
            title="Last Accessed",
            description="Timestamp indicating when the session was last accessed.",
        ),
    ]
    data: Annotated[
        dict,
        Field(
            default_factory=dict,
            title="Session Data",
            description="Additional data associated with the session.",
        ),
    ]
