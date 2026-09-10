from pydantic import BaseModel, EmailStr, Field
from app.models import UserRole+


class UserBase:
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=50)


class UserResponse(UserBase):
    id: int
    role: UserRole

    class Config:
        from_attributes = True