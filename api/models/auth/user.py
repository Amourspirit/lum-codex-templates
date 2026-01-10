from typing import Optional
from pydantic import BaseModel


class User(BaseModel):
    username: str
    name: str
    email: str
    roles: list[str]
    hashed_pwd: str
    is_active: bool
    monad_name: Optional[str] = None
