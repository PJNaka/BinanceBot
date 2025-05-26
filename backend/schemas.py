# backend/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    email: EmailStr # email-validator will be used by pydantic

class UserCreate(UserBase):
    password: str

class User(UserBase): # For reading/returning user data
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # Pydantic's ORM mode will tell Pydantic to read the data even if it is not a dict, but an ORM model

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None 
    # Or could use user_id: Optional[int] = None, depending on what you store in JWT 'sub'
