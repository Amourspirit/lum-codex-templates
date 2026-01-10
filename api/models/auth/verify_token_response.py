from pydantic import BaseModel


class VerifyTokenResponse(BaseModel):
    valid: bool
    username: str
    name: str
    email: str
    roles: list[str]
