from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import timedelta

from app.database import get_db
from app.models import User, Service, Booking
from app.schemas import UserCreate, UserResponse, ServiceCreate, ServiceResponse, BookingCreate, BookingResponse
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

# ЭНДПОИНТ СОЗДАНИЯ ЗАПИСИ (БРОНИРОВАНИЯ)
@app.post("/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(booking_data: BookingCreate, db: AsyncSession = Depends(get_db)):
    service_query = select(Service).where(Service.id == booking_data.service_id)
    service_result = await db.execute(service_query)
    service = service_result.scalar_one_or_none()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Указанная услуга не найдена"
        )

    calculated_end_time = booking_data.start_time + timedelta(minutes=service.duration_minutes)

    new_booking = Booking(
        client_id=booking_data.client_id,
        master_id=booking_data.master_id,
        service_id=booking_data.service_id,
        start_time=booking_data.start_time,
        end_time=calculated_end_time,
        status="created"
    )

    db.add(new_booking)
    await db.commit()

    return BookingResponse(
        client_id=new_booking.client_id,
        master_id=new_booking.master_id,
        service_id=new_booking.service_id,
        start_time=new_booking.start_time,
        end_time=calculated_end_time,
        id=new_booking.id or 1,
        status=new_booking.status
    )