from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=255)


class UserSummary(BaseModel):
    id: int
    username: str
    role: str


class LoginData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserSummary
