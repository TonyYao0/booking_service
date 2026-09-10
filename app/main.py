from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse

app = FastAPI(
    title="Сервис по бронированию",
    description="Бэкенд для автоматизации записи",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {
        "status": "working",
        "message": "Добро пожаловать в API системы бронирования!"
    }

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
   query = select(User).where(User.email == user_data.email)
   result = await db.execute(query)
   existing_user = result.scalar_one_or_none()

   if existing_user:
       raise HTTPException(
           status_code=status.HTTP_400_BAD_REQUEST,
           detail="Пользователь с таким email уже зарегистрирован"
       )
   new_user = User(
       email=user_data.email,
       full_name=user_data.full_name,
       hashed_password=user_data.password,
   )

   db.add(new_user)
   await db.commit()
   await db.refresh(new_user)

   return new_user