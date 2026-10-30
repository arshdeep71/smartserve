from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = "admin"


class LoginRequest(BaseModel):
    password: str


class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str
