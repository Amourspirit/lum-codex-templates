from pydantic import BaseModel
from typing import Optional


class UserResponse(BaseModel):
    username: str
    name: str
    email: str
    roles: list[str]
    is_active: bool
    monad_name: Optional[str] = None

    class Config:
        from_attributes = True
