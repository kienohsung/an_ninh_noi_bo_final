from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class UserBase(BaseModel):
    username: str
    full_name: str
    role: str

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    telegram_id: Optional[str] = None

class UserRead(UserBase):
    id: int
    telegram_id: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
