from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    wallet_address: str
    is_active: bool
    balance: float
    created_at: datetime

    class Config:
        orm_mode = True