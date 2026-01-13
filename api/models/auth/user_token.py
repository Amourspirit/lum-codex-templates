from pydantic import BaseModel, Field
from typing import Annotated


class Token(BaseModel):
    access_token: Annotated[
        str, Field(title="Access Token", description="The access token string.")
    ]
    token_type: Annotated[
        str,
        Field(title="Token Type", description="The type of the token, e.g., 'bearer'."),
    ]
