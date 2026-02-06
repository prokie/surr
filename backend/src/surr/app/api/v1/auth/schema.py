from pydantic import BaseModel, Field

from surr.app.schema.user import UserBase


class UserRead(UserBase):
    id: int


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128, pattern=r"^\S+$")


class Token(BaseModel):
    access_token: str
    token_type: str
