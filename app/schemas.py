from pydantic import BaseModel, EmailStr, Field
from app.models import UserRole

# Базовые поля пользователя
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)

# Что принимает сервер при регистрации от клиента
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=50)

# What сервер отдает обратно клиенту (без пароля!)
class UserResponse(UserBase):
    id: int
    role: UserRole

    class Config:
        from_attributes = True


class ServiceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    duration_minutes: int = Field(..., gt=0, lt=480)  # от 1 минуты до 8 часов
    price: int = Field(..., ge=0)  # цена не может быть отрицательной

class ServiceCreate(ServiceBase):
    pass

class ServiceResponse(ServiceBase):
    id: int

    class Config:
        from_attributes = True