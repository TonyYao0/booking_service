from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.api_client import login, get_my_bookings

router = Router()


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Записаться")],
            [KeyboardButton(text="📋 Мои брони")],
            [KeyboardButton(text="🚪 Выйти")],
        ],
        resize_keyboard=True,
    )


class LoginStates(StatesGroup):
    waiting_email = State()
    waiting_password = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"👋 Привет, <b>{message.from_user.full_name}</b>!\n\n"
        "Я бот сервиса бронирования. Помогу записаться к мастеру.\n\n"
        "Нажмите «📝 Записаться», чтобы начать.",
        reply_markup=main_menu(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🤖 <b>Доступные команды:</b>\n\n"
        "/start — начать заново\n"
        "/help — справка"
    )


@router.message(F.text == "🚪 Выйти")
async def cmd_logout(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🔒 Вы вышли. Для входа — /start.",
        reply_markup=main_menu(),
    )


@router.message(F.text == "📝 Записаться")
async def start_booking(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("token"):
        from app.handlers.booking import start_booking_flow
        await start_booking_flow(message, state)
        return
    await state.set_state(LoginStates.waiting_email)
    await message.answer("🔐 Введите ваш <b>email</b>:")


@router.message(LoginStates.waiting_email)
async def process_email(message: Message, state: FSMContext):
    email = (message.text or "").strip()
    if "@" not in email:
        await message.answer("⚠️ Похоже, это не email. Попробуйте ещё раз:")
        return
    await state.update_data(email=email)
    await state.set_state(LoginStates.waiting_password)
    await message.answer("🔑 Введите пароль:")


@router.message(LoginStates.waiting_password)
async def process_password(message: Message, state: FSMContext):
    password = (message.text or "").strip()
    data = await state.get_data()
    email = data.get("email")
    try:
        await message.delete()
    except Exception:
        pass
    await message.answer("⏳ Проверяю...")
    token = await login(email, password)
    if not token:
        await state.clear()
        await message.answer(
            "🔴 Неверный email или пароль.",
            reply_markup=main_menu(),
        )
        return
    await state.update_data(token=token)
    await state.set_state(None)
    await message.answer("✅ Вы вошли!", reply_markup=main_menu())
    from app.handlers.booking import start_booking_flow
    await start_booking_flow(message, state)


@router.message(F.text == "📋 Мои брони")
async def my_bookings(message: Message, state: FSMContext):
    data = await state.get_data()
    token = data.get("token")
    if not token:
        await message.answer(
            "🔐 Сначала войдите: «📝 Записаться».",
            reply_markup=main_menu(),
        )
        return
    bookings = await get_my_bookings(token)
    if not bookings:
        await message.answer(
            "📭 У вас пока нет бронирований.",
            reply_markup=main_menu(),
        )
        return
    from app.handlers.booking import pretty_date
    lines = ["📋 <b>Ваши брони:</b>\n"]
    for b in bookings:
        status = b.get("status") or "active"
        icon = {
            "created": "🟡",
            "confirmed": "🟢",
            "completed": "🔵",
            "cancelled": "🔴",
        }.get(status, "⚪")
        lines.append(
            f"{icon} #{b.get('id')} — {pretty_date(b.get('start_time'))}\n"
            f"   Услуга #{b.get('service_id')} · "
            f"Мастер #{b.get('master_id')} · {status}\n"
        )
    await message.answer("\n".join(lines), reply_markup=main_menu())