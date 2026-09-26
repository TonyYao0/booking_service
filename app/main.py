from datetime import timedelta, datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.security import OAuth2PasswordRequestForm

from app.database import get_db
from app.models import User, Service, Booking
from app.schemas import UserCreate, UserResponse, ServiceCreate, ServiceResponse, BookingCreate, BookingResponse, UserLogin, Token, BookingStatusUpdate
from app.auth import get_password_hash, verify_password, create_access_token, verify_access_token, oauth2_scheme


app = FastAPI(
    title="Сервис по бронированию",
    description="Бэкенд для автоматизации записи",
    version="1.0.0"
)

# 1. ЗАВИСИМОСТЬ ДЛЯ ПРОВЕРКИ ТОКЕНА (ТЕПЕРЬ НАВЕРХУ)
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось валидировать учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_access_token(token, credentials_exception)

    query = select(User).where(User.id == token_data["user_id"])
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user

# КЛАСС ДЛЯ ПРОВЕРКИ РОЛЕЙ ПОЛЬЗОВАТЕЛЯ
class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)):
        user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        if "." in user_role:
            user_role = user_role.split(".")[-1]
            
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас недостаточно прав для выполнения этого действия"
            )
        return current_user


# 2. ПУБЛИЧНЫЕ ЭНДПОИНТЫ API
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

@app.post("/auth/login", response_model=Token)
async def login_for_access_token(login_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    query = select(User).where(User.email == login_data.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get('/auth/me', response_model=UserResponse)
async def get_current_user_principal(
    current_user: User = Depends(get_current_user)
):
    return current_user


@app.post("/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(service_data: ServiceCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(RoleChecker(["admin", "master"]))):
    new_service = Service(
        name=service_data.name,
        duration_minutes=service_data.duration_minutes,
        price=service_data.price
    )
    db.add(new_service)
    await db.commit()
    await db.refresh(new_service)
    return new_service

@app.get("/services", response_model=list[ServiceResponse])
async def get_services(db: AsyncSession = Depends(get_db)):
    query = select(Service)
    result = await db.execute(query)
    services = result.scalars().all()
    return services


# 3. ЗАЩИЩЕННЫЙ ЭНДПОИНТ БРОНИРОВАНИЯ
@app.post("/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_time = datetime.now(timezone.utc)
    booking_start = booking_data.start_time.replace(tzinfo=timezone.utc)

    if booking_start < current_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно создать бронирование на прошедшее время"
        )
    
    service_query = select(Service).where(Service.id == booking_data.service_id)
    service_result = await db.execute(service_query)
    service = service_result.scalar_one_or_none()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Указанная услуга не найдена"
        )

    calculated_end_time = booking_data.start_time + timedelta(minutes=service.duration_minutes)

    conflict_query = select(Booking).where(
        Booking.master_id == booking_data.master_id,
        Booking.status != 'cancelled',
        booking_data.start_time <= Booking.end_time,
        calculated_end_time > Booking.start_time
    )

    conflict_results = await db.execute(conflict_query)
    existing_conflicts = conflict_results.scalar_one_or_none()

    if existing_conflicts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Выбранное время уже занято у этого мастера другим бронированием"
        )

     # Создаем новую запись в таблице Bookings
    new_booking = Booking(
        client_id=current_user.id,
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

@app.post("/auth/login", response_model=Token)
async def login_for_access_token(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    query = select(User).where(User.email ==login_data.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    return{"access_token": access_token, "token_type": "bearer"}

@app.get("/bookings/my", response_model=list[BookingResponse])
async def get_my_bookings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Booking).where(Booking.client_id == current_user.id)
    result = await db.execute(query)
    bookings = result.scalars().all()
    return bookings

# ЭНДПОИНТ ПОЛУЧЕНИЯ РАСПИСАНИЯ ДЛЯ ТЕКУЩЕГО МАСТЕРА
@app.put("/bookings/master", response_model=list[BookingResponse])
async def get_master_booking(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
     # Делаем SQL-запрос: "Выбери все записи из таблицы bookings, где master_id равен ID текущего вошедшего пользователя"
    query = select(Booking).where(Booking.master_id == current_user.id)
    result = await db.execute(query)

    bookings = result.scalars().all()
    return bookings

@app.delete('/delete/{booking_id}', status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Booking).where(Booking.id == booking_id)
    result = await db.execut(query)
    booking = result.scalar_one_or_non()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUN,
            detail="Указано не верное бронирование"
        )
    await db.delet(booking)
    await db.commit()

    return None

@app.patch("/services/{service_id}", response_model=ServiceResponse)
async def update_services (
    service_id: int,
    service_data: ServiceCreate,
    db:AsyncSession = Depends (get_db),
    current_user: User = Depends(RoleChecker(["admin", "master"]))
):
    query = select(Service).where(Service.id==service_id)
    result = await db.execute(query)
    service=result.scalar_one_or_none()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Не удалось найти указанную запись'
        )
    service.name = service_data.name
    service.price = service_data.price
    service.duration_minutes = service_data.duration_minutes

    await db.commit()
    await db.refresh(service)

    return service

@app.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: int,
    db: AsyncSession = Depends (get_db),
    current_user: User = Depends(RoleChecker(["admin", "master"]))
):
    query = select(Service).where(Service.id == service_id)
    result = await db.execute(query)
    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='Не удалось найти указанную запись'
                )
    await db.delete(service)
    await db.commit()
    return None

@app.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking_details(
    booking_id:int,
    db : AsyncSession = Depends(get_db),
    current_user: User =Depends(get_current_user)
):
    query = select(Booking).where(Booking.id == booking_id)
    result = await db.execute(query)
    booking = result.scalar_one_or_none()



    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Букинга с id {id} нет в базе данных"
        )
    user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if "." in user_role:
        user_role = user_role.split(".")[-1]

    if user_role == "client" and booking.client_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас недостаточно прав для просмотра этой записи."
        )
    return booking

@app.patch("/bookings/{booking_id}/status", response_model=BookingResponse)
async def update_booking_status (
    booking_id: int,
    status_data: BookingStatusUpdate,
    db:AsyncSession = Depends(get_db),
    current_user:User = Depends(get_current_user)
):
    query = select(Booking).where(Booking.id == booking_id)
    result = await db.execute(query)
    booking  = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Указанная бронь не найдена"
            )
    booking.status = status_data.status

    await db.commit()
    await db.refresh(booking)

    return booking

@app.get("/bookings", response_model=list[BookingResponse])
async def get_all_bookins(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["admin"]))
):
    query = select(Booking)
    result = await db.execute(query)
    bookings = result.scalars().all()

    return bookings

