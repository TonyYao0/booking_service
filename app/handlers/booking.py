from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.api_client import get_services, get_masters, create_booking
from app.handlers.start import main_menu

router = Router()


class BookingStates(StatesGroup):
    choosing_service = State()
    choosing_master = State()
    choosing_date = State()
    choosing_time = State()
    confirming = State()


def pretty_date(iso_str) -> str:
    if not iso_str:
        return "Дата не указана"
    try:
        cleaned = iso_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        return dt.strftime("%d.%m.%Y в %H:%M")
    except Exception:
        return str(iso_str)


async def start_booking_flow(message: Message, state: FSMContext):
    services = await get_services()
    if not services:
        await message.answer(
            "😔 Нет доступных услуг.",
            reply_markup=main_menu(),
        )
        return
    active = [s for s in services if s.get("is_active", True)]
    if not active:
        await message.answer(
            "😔 Нет активных услуг.",
            reply_markup=main_menu(),
        )
        return
    buttons = [
        [InlineKeyboardButton(
            text=f"{s['name']} · {s['price']} ₽ · {s['duration_minutes']} мин",
            callback_data=f"svc:{s['id']}",
        )]
        for s in active
    ]
    await state.set_state(BookingStates.choosing_service)
    await message.answer(
        "💅 <b>Шаг 1/4.</b> Выберите услугу:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("svc:"))
async def on_service_chosen(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split(":")[1])
    await state.update_data(service_id=service_id)

    masters = await get_masters()
    if not masters:
        await callback.message.edit_text("😔 Нет мастеров.")
        await state.set_state(None)
        await callback.answer()
        return

    buttons = [
        [InlineKeyboardButton(
            text=m["full_name"],
            callback_data=f"mst:{m['id']}",
        )]
        for m in masters
    ]
    await state.set_state(BookingStates.choosing_master)
    await callback.message.edit_text(
        "👨‍🔧 <b>Шаг 2/4.</b> Выберите мастера:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mst:"))
async def on_master_chosen(callback: CallbackQuery, state: FSMContext):
    master_id = int(callback.data.split(":")[1])
    await state.update_data(master_id=master_id)

    today = datetime.now().date()
    buttons = []
    row = []
    for i in range(1, 11):
        d = today + timedelta(days=i)
        row.append(InlineKeyboardButton(
            text=d.strftime("%d.%m"),
            callback_data=f"dt:{d.isoformat()}",
        ))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    await state.set_state(BookingStates.choosing_date)
    await callback.message.edit_text(
        "📅 <b>Шаг 3/4.</b> Выберите дату:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dt:"))
async def on_date_chosen(callback: CallbackQuery, state: FSMContext):
    date_str = callback.data.split(":", 1)[1]
    await state.update_data(date=date_str)

    buttons = []
    row = []
    for h in range(9, 21):
        row.append(InlineKeyboardButton(
            text=f"{h:02d}:00",
            callback_data=f"tm:{h:02d}:00",
        ))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    await state.set_state(BookingStates.choosing_time)
    await callback.message.edit_text(
        "🕐 <b>Шаг 4/4.</b> Выберите время:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tm:"))
async def on_time_chosen(callback: CallbackQuery, state: FSMContext):
    time_str = callback.data.split(":", 1)[1]
    await state.update_data(time=time_str)

    data = await state.get_data()
    start_time = f"{data['date']}T{time_str}:00"
    await state.update_data(start_time=start_time)

    buttons = [[
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm:yes"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="confirm:no"),
    ]]
    await state.set_state(BookingStates.confirming)
    await callback.message.edit_text(
        f"📋 <b>Проверьте:</b>\n\n"
        f"💅 Услуга: #{data['service_id']}\n"
        f"👨‍🔧 Мастер: #{data['master_id']}\n"
        f"📅 {pretty_date(start_time)}\n\n"
        f"Всё верно?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data == "confirm:yes")
async def on_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    token = data.get("token")
    if not token:
        await callback.message.edit_text("🔐 Сессия истекла. /start")
        await state.clear()
        await callback.answer()
        return

    await callback.message.edit_text("⏳ Создаю...")
    status, resp = await create_booking(
        token,
        data["service_id"],
        data["master_id"],
        data["start_time"],
    )

    if status == 201:
        await callback.message.edit_text(
            f"🎉 <b>Бронь создана!</b>\n\n"
            f"📅 {pretty_date(data['start_time'])}\n"
            f"💅 Услуга #{data['service_id']}\n"
            f"👨‍🔧 Мастер #{data['master_id']}\n"
            f"Статус: 🟡 created"
        )
    else:
        err = resp.get("detail") if isinstance(resp, dict) else str(resp)
        await callback.message.edit_text(
            f"🔴 Ошибка: {err}\n\nПопробуйте другое время."
        )

    await state.set_state(None)
    await callback.answer()


@router.callback_query(F.data == "confirm:no")
async def on_cancel(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await callback.message.edit_text("❌ Отменено.")
    await callback.answer()