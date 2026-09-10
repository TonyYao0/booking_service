from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models import User, Service
from app.schemas import UserCreate, UserResponse, ServiceCreate, ServiceResponse
from app.auth import get_password_hash

app = FastAPI(
    title="Сервис по бронированию",
    description="Бэкенд для автоматизации записи",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"status": "working", "message": "Добро пожаловать в API!"}

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
        hashed_password=get_password_hash(user_data.password),
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

# Эндпоинт добавления новой услуги (POST)
@app.post("/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(service_data: ServiceCreate, db: AsyncSession = Depends(get_db)):
    new_service = Service(
        name=service_data.name,
        duration_minutes=service_data.duration_minutes,
        price=service_data.price
    )
    db.add(new_service)
    await db.commit()
    await db.refresh(new_service)
    return new_service


# Эндпоинт получения списка всех услуг (GET)
@app.get("/services", response_model=list[ServiceResponse])
async def get_services(db: AsyncSession = Depends(get_db)):
    query = select(Service)
    result = await db.execute(query)
    services = result.scalars().all()
    return services