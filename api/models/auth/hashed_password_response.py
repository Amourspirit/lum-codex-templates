from pydantic import BaseModel


class HashedPasswordResponse(BaseModel):
    hashed_password: str
