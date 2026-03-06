from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.user import Role
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: Role = Role.USER

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[Role] = None

class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
