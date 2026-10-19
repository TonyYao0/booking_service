# 🗓️ Booking Service — Асинхронный сервис бронирования и записи

Полноценная система автоматизации онлайн-записи к мастерам (салоны красоты, автосервисы, частная практика) с **REST API на FastAPI** и **интерактивным UI на Flet**.

Поддерживает три роли (клиент / мастер / администратор), управление услугами с soft-delete, полноценные личные кабинеты и JWT-авторизацию.

---

## 📑 Содержание

- [Возможности](#-возможности)
- [Стек технологий](#-стек-технологий)
- [Архитектура](#-архитектура-проекта)
- [Установка](#-установка-и-запуск)
- [Тестовые аккаунты](#-тестовые-учётные-записи)
- [API-эндпоинты](#-api-эндпоинты)
- [Роли и права](#-роли-и-права)
- [Статусы брони](#-статусы-бронирования)
- [Soft-delete](#-soft-delete-услуг)
- [Примеры curl](#-примеры-работы)
- [Roadmap](#-возможные-улучшения)
- [Лицензия](#-лицензия)

---

## 🚀 Возможности

### 🔐 Безопасность и авторизация
- **JWT-токены (OAuth2)** с ограниченным сроком жизни
- **bcrypt** для хэширования паролей
- **RBAC** — ролевая модель на `client`, `master`, `admin`
- Защита эндпоинтов через dependency `get_current_user`
- Смена пароля через `PATCH /auth/me/password`

### 📅 Бизнес-логика расписания
- Автоматический расчёт времени окончания услуги по её длительности
- Запрет создания брони на прошедшее время
- Блокировка пересекающихся слотов у одного мастера
- Ограничение рабочих часов (9:00–21:00) на фронтенде

### 🎨 Интерактивный UI на Flet
- **Форма входа и регистрации** с клиентской валидацией
- **Клиентский кабинет:**
  - создание брони (услуга + мастер + дата + время)
  - список своих записей
  - отмена с подтверждением в диалоге
  - профиль + смена пароля
- **Кабинет мастера:**
  - список записей к нему
  - кнопки **Подтвердить / Завершить / Отменить**
- **Админ-панель:**
  - управление услугами (создание, скрытие, восстановление)
  - список пользователей с ролями
  - все брони в системе
- Персонализация: приветствие по имени, аватар, SnackBar-уведомления

### 🗃️ Управление данными
- Фильтрация услуг по цене: `min_price`, `max_price`
- Пагинация: `limit`, `offset` для броней
- **Soft-delete услуг** — «удаление» превращается в скрытие (`is_active = False`), история броней сохраняется
- Восстановление скрытых услуг через `POST /services/{id}/restore`
- **Защита целостности:** нельзя удалить услугу с активными бронированиями

### ⚙️ Инфраструктура
- Секреты в `.env` через `Pydantic Settings`
- Миграции через **Alembic**
- Полная асинхронность: SQLAlchemy 2.0 + asyncpg + httpx

---

## 🛠️ Стек технологий

### Бэкенд
| Компонент | Версия / Назначение |
|---|---|
| Python | 3.12+ |
| FastAPI | асинхронный веб-фреймворк |
| SQLAlchemy | 2.0 (Async ORM) |
| asyncpg | асинхронный драйвер PostgreSQL |
| PostgreSQL | СУБД |
| Pydantic | v2 + Pydantic Settings |
| Alembic | миграции |
| PyJWT + bcrypt | безопасность |

### Фронтенд
| Компонент | Версия / Назначение |
|---|---|
| Flet | 1.0.3 (кроссплатформенный UI на Python) |
| httpx | асинхронный HTTP-клиент |

---

## 📋 Архитектура проекта

```text
booking_service/
├── alembic/                # История миграций БД
│   └── versions/
├── app/                    # Бэкенд
│   ├── config.py           # Pydantic Settings, чтение .env
│   ├── database.py         # Async SQLAlchemy engine + get_db
│   ├── models.py           # User, Service (+ is_active), Booking
│   ├── schemas.py          # Pydantic-схемы
│   ├── auth.py             # bcrypt, JWT, oauth2_scheme
│   └── main.py             # FastAPI-приложение, эндпоинты
├── frontend/               # Flet-приложение
│   └── main.py             # Авторизация, кабинеты, админка
├── .env                    # Секреты (не коммитится)
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

**Схема БД (упрощённо):**

```text
┌──────────┐        ┌──────────┐        ┌──────────┐
│  users   │───────<│ bookings │>───────│ services │
└──────────┘        └──────────┘        └──────────┘
 id, email,          id,                 id, name,
 full_name,          client_id (FK),     price,
 hashed_password,    master_id (FK),     duration_minutes,
 role                service_id (FK),    is_active
                     start_time,
                     end_time,
                     status
```

---

## ⚙️ Установка и запуск

### 1. Клонирование и виртуальное окружение

```bash
git clone https://github.com/TonyYao0/booking_service.git
cd booking_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Настройка `.env`

Создайте файл `.env` в корне проекта:

```env
SECRET_KEY=SUPER_SECRET_KEY_CHANGE_ME_IN_PRODUCTION
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/booking_db
```

> ⚠️ **Порт `5433`** — если у вас стандартный PostgreSQL, замените на `5432`.
>
> ⚠️ **SECRET_KEY** — сгенерируйте нормальный:
> ```bash
> python -c "import secrets; print(secrets.token_urlsafe(48))"
> ```

### 3. База данных и миграции

```bash
# Запуск PostgreSQL
sudo service postgresql start

# Создание БД (если её нет)
sudo -u postgres createdb booking_db

# Применение миграций
alembic upgrade head
```

> Если Alembic не настроен — создайте таблицы вручную:
> ```bash
> python -c "
> import asyncio
> from app.database import engine
> from app.models import Base
> async def init():
>     async with engine.begin() as conn:
>         await conn.run_sync(Base.metadata.create_all)
> asyncio.run(init())
> "
> ```

### 4. Запуск бэкенда (Терминал 1)

```bash
cd ~/booking_service
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Swagger UI:** http://localhost:8000/docs

### 5. Запуск фронтенда (Терминал 2)

```bash
cd ~/booking_service
source venv/bin/activate
python frontend/main.py
```

Flet откроет браузер на **http://127.0.0.1:8500**.

### 📌 Проверка, что всё работает

```bash
# Бэкенд жив
curl http://127.0.0.1:8000/

# Swagger открывается
# http://127.0.0.1:8000/docs

# Фронт открывается
# http://127.0.0.1:8500
```

---

## 👤 Тестовые учётные записи

| Email | Пароль | Роль | Что видит |
|---|---|---|---|
| `anna@example.com` | `mytestpassword123` | **ADMIN** | Админ-панель: услуги, пользователи, брони |
| `user2@example.com` | `newpass123` | **MASTER** | Кабинет мастера: записи к нему |
| `testclient@example.com` | `mytestpassword123` | **CLIENT** | Клиентский кабинет |
| `user45@example.com` | `newpass123` | ADMIN | — |

### Как сбросить пароль

```bash
# 1. Сгенерировать bcrypt-хеш
python -c "import bcrypt; print(bcrypt.hashpw(b'newpass123', bcrypt.gensalt()).decode())"

# 2. Скопировать хеш и выполнить:
psql -h 127.0.0.1 -p 5433 -U postgres -d booking_db -c \
  "UPDATE users SET hashed_password = 'ХЕШ' WHERE email = 'user2@example.com';"
```

### Как сменить роль

```bash
psql -h 127.0.0.1 -p 5433 -U postgres -d booking_db -c \
  "UPDATE users SET role = 'ADMIN' WHERE email = 'anna@example.com';"
```

> ⚠️ В БД роли хранятся **ЗАГЛАВНЫМИ**: `CLIENT`, `MASTER`, `ADMIN`.

---

## 📡 API-эндпоинты

### 🌐 Публичные

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/` | Проверка работы сервиса |
| `POST` | `/auth/register` | Регистрация нового пользователя |
| `POST` | `/auth/login` | Получение JWT-токена |
| `GET` | `/services` | Список **активных** услуг (с фильтрами) |
| `GET` | `/masters` | Список мастеров |

### 👤 Профиль (требует JWT)

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/auth/me` | Текущий пользователь |
| `PATCH` | `/auth/me` | Обновление `full_name` |
| `PATCH` | `/auth/me/password` | Смена пароля |

### 📅 Бронирования (требует JWT)

| Метод | Путь | Роль | Описание |
|---|---|---|---|
| `POST` | `/bookings` | client | Создать бронь |
| `GET` | `/bookings/my` | client | Свои брони (пагинация) |
| `GET` | `/bookings/master` | master | Записи к мастеру |
| `GET` | `/bookings/{id}` | любой | Детали брони |
| `PATCH` | `/bookings/{id}/status` | client/master/admin | Смена статуса |
| `DELETE` | `/bookings/{id}` | client/admin | Отмена брони |
| `GET` | `/bookings` | admin | Все брони |

### 💅 Управление услугами (RBAC)

| Метод | Путь | Роль | Описание |
|---|---|---|---|
| `POST` | `/services` | admin | Создать услугу |
| `PATCH` | `/services/{id}` | admin/master | Обновить услугу |
| `DELETE` | `/services/{id}` | admin | **Soft-delete** (скрыть) |
| `GET` | `/services/all` | admin | Все услуги (включая скрытые) |
| `POST` | `/services/{id}/restore` | admin | Восстановить услугу |

### 👥 Управление пользователями (admin)

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/users` | Все пользователи |
| `PATCH` | `/users/{id}/role` | Сменить роль |

---

## 🎭 Роли и права

| Возможность | CLIENT | MASTER | ADMIN |
|---|:---:|:---:|:---:|
| Просмотр своих броней | ✅ | — | ✅ |
| Создание брони | ✅ | — | ✅ |
| Отмена своей брони | ✅ | — | ✅ |
| Просмотр записей к мастеру | — | ✅ | — |
| Подтверждение / завершение брони | — | ✅ | ✅ |
| Смена статуса чужой брони | — | — | ✅ |
| Управление услугами | — | — | ✅ |
| Список всех пользователей | — | — | ✅ |
| Смена ролей | — | — | ✅ |

---

## 🔄 Статусы бронирования

```text
   ┌─────────┐    master    ┌───────────┐    master    ┌───────────┐
   │ created │─────────────▶│ confirmed │─────────────▶│ completed │
   └─────────┘              └───────────┘              └───────────┘
        │                        │
        │ client/master          │ client/master
        ▼                        ▼
   ┌─────────────────────────────────┐
   │           cancelled             │
   └─────────────────────────────────┘
```

- **`created`** — только что создана клиентом
- **`confirmed`** — мастер подтвердил
- **`completed`** — услуга оказана
- **`cancelled`** — отменена клиентом или мастером

---

## 🗃️ Soft-delete услуг

При «удалении» услуги:

1. `is_active = False` (физического удаления нет)
2. Услуга исчезает из `GET /services` — клиенты её не видят
3. Остаётся в БД для истории броней
4. Видна админу через `GET /services/all`
5. Может быть восстановлена через `POST /services/{id}/restore`

**Зачем так:** физическое удаление услуги сломало бы связи с существующими бронями (FK constraint `RESTRICT`).

```text
┌─────────────────────┐         ┌─────────────────────┐
│ is_active = true    │         │ is_active = false   │
│ (в GET /services)   │◀───────▶│ (только в /all)     │
│ видят клиенты       │  soft-  │ видят админы        │
│                     │  delete │                     │
└─────────────────────┘         └─────────────────────┘
```

---

## 🧪 Примеры работы

### Логин и получение токена

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testclient@example.com&password=mytestpassword123" \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "Token: ${TOKEN:0:40}..."
```

### Список услуг

```bash
curl -s http://127.0.0.1:8000/services | python -m json.tool
```

### Создать бронь

```bash
curl -X POST http://127.0.0.1:8000/bookings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 0,
    "master_id": 2,
    "service_id": 1,
    "start_time": "2026-10-25T14:00:00"
  }'
```

### Свои брони

```bash
curl -s http://127.0.0.1:8000/bookings/my \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

### Смена пароля

```bash
curl -X PATCH http://127.0.0.1:8000/auth/me/password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_password": "mytestpassword123", "new_password": "newpass456"}'
```

### Soft-delete услуги (админ)

```bash
ADMIN_TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=anna@example.com&password=mytestpassword123" \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Скрыть
curl -X DELETE http://127.0.0.1:8000/services/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Восстановить
curl -X POST http://127.0.0.1:8000/services/1/restore \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## 🧑‍💻 Разработка

### Полезные команды

```bash
# Миграции
alembic revision --autogenerate -m "описание"
alembic upgrade head

# Посмотреть БД
psql -h 127.0.0.1 -p 5433 -U postgres -d booking_db
\dt
SELECT * FROM users;
SELECT id, name, is_active FROM services;

# Проверка синтаксиса
python -m py_compile app/main.py
python -m py_compile frontend/main.py
```

---

## 💡 Возможные улучшения

- [ ] Уведомления (email/push) о новых бронях
- [ ] Календарь-вид для расписания мастера
- [ ] Смена роли через UI админ-панели
- [ ] Экспорт данных в CSV
- [ ] Docker-compose для быстрого развёртывания
- [ ] Полноценные тесты (pytest + httpx)
- [ ] CI/CD через GitHub Actions
- [ ] Rate limiting на `/auth/login`
- [ ] Refresh-токены

---

## ❓ FAQ

**Q: Не могу залогиниться — 401.**
A: Проверьте пароль. Если забыли — сбросьте через `bcrypt` + `psql` (см. раздел «Тестовые учётные записи»).

**Q: `column "is_active" does not exist`.**
A: Примените миграцию:
```bash
psql -h 127.0.0.1 -p 5433 -U postgres -d booking_db \
  -c "ALTER TABLE services ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;"
```

**Q: `WebSocketDisconnect(code=1006)` в логах.**
A: Нормально — браузер разорвал соединение при F5 или перезапуске фронта. На работу не влияет.

**Q: Frontend не открывается — пустой экран.**
A: Смотрите терминал `python frontend/main.py` — там будет трейсбек. Чаще всего — синтаксическая ошибка.

**Q: `Cannot connect to database`.**
A: Проверьте:
```bash
sudo service postgresql status
psql -h 127.0.0.1 -p 5433 -U postgres -d booking_db -c "\dt"
```

---

## 📄 Лицензия

MIT — используйте свободно в личных и коммерческих проектах.

*Проект создан в рамках изучения FastAPI + Flet. Pull requests приветствуются.*