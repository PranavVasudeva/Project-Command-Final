from datetime import datetime

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    portal_role: Literal["CIVILIAN", "OFFICER", "RESPONSE_TEAM"] | None = None


class UserPublic(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: str
    created_at: datetime