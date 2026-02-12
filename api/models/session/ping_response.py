from typing import Annotated
from pydantic import BaseModel, Field


class PingResponse(BaseModel):
    message: Annotated[
        str,
        Field(
            title="Message", description="A message related to the ping. Expect 'pong'."
        ),
    ]
