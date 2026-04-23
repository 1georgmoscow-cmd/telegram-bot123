from datetime import date, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.database.db import Database
from app.keyboards.admin import admin_menu_kb, bookings_manage_kb, slots_manage_kb
from app.keyboards.calendar import format_ru_date, month_calendar_kb
from app.keyboards.common import back_to_menu_kb
from app.services.scheduler import ReminderService
from app.states.admin import AdminStates

router = Router()


def _is_admin(user_id: int, settings: Settings) -> bool:
    return user_id == settings.admin_id


def _is_valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery, settings: Settings, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(
        "<b>Админ-панель</b>\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=admin_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_day")
async def admin_add_day_start(
    callback: CallbackQuery, settings: Settings, state: FSMContext
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_add_day)
    await callback.message.edit_text(
        "Введите дату рабочего дня в формате <code>YYYY-MM-DD</code>.",
        parse_mode="HTML",
        reply_markup=back_to_menu_kb(),
    )
    await callback.answer()


@router.message(AdminStates.waiting_add_day)
async def admin_add_day_save(message: Message, db: Database, state: FSMContext) -> None:
    day = message.text.strip()
    if not _is_valid_date(day):
        await message.answer("Неверный формат даты. Используйте YYYY-MM-DD.")
        return
    db.add_work_day(day)
    await state.clear()
    await message.answer("Рабочий день добавлен.", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin_add_slot")
async def admin_add_slot_start(
    callback: CallbackQuery, settings: Settings, state: FSMContext
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_add_slot_date)
    await callback.message.edit_text(
        "Введите дату для добавления слота: <code>YYYY-MM-DD</code>",
        parse_mode="HTML",
        reply_markup=back_to_menu_kb(),
    )
    await callback.answer()


@router.message(AdminStates.waiting_add_slot_date)
async def admin_add_slot_get_date(message: Message, state: FSMContext) -> None:
    slot_date = message.text.strip()
    if not _is_valid_date(slot_date):
        await message.answer("Неверный формат даты. Используйте YYYY-MM-DD.")
        return
    await state.update_data(slot_date=slot_date)
    await state.set_state(AdminStates.waiting_add_slot_time)
    await message.answer("Введите время слота: <code>HH:MM</code>", parse_mode="HTML")


@router.message(AdminStates.waiting_add_slot_time)
async def admin_add_slot_save(message: Message, db: Database, state: FSMContext) -> None:
    data = await state.get_data()
    slot_date = data["slot_date"]
    slot_time = message.text.strip()
    if len(slot_time) != 5 or slot_time[2] != ":":
        await message.answer("Неверный формат времени. Используйте HH:MM.")
        return
    db.add_slot(slot_date, slot_time)
    await state.clear()
    await message.answer("Слот добавлен.", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin_delete_slot")
async def admin_delete_slot_start(
    callback: CallbackQuery, settings: Settings, state: FSMContext
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_delete_slot_date)
    await callback.message.edit_text(
        "Введите дату, где нужно удалить слот: <code>YYYY-MM-DD</code>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.waiting_delete_slot_date)
async def admin_delete_slot_date(message: Message, db: Database, state: FSMContext) -> None:
    date_str = message.text.strip()
    if not _is_valid_date(date_str):
        await message.answer("Неверный формат даты. Используйте YYYY-MM-DD.")
        return
    slots = db.get_free_slots(date_str)
    if not slots:
        await message.answer("Свободные слоты не найдены.", reply_markup=admin_menu_kb())
        await state.clear()
        return
    await state.clear()
    await message.answer(
        "Выберите слот для удаления:",
        reply_markup=slots_manage_kb("admin_delete_slot_pick", date_str, slots),
    )


@router.callback_query(F.data.startswith("admin_delete_slot_pick:"))
async def admin_delete_slot_pick(callback: CallbackQuery, db: Database, settings: Settings) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return
    _, date_str, time_str = callback.data.split(":")
    changed = db.delete_slot(date_str, time_str)
    if changed:
        await callback.message.edit_text("Слот удален.", reply_markup=admin_menu_kb())
    else:
        await callback.message.edit_text("Слот не найден.", reply_markup=admin_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "admin_close_day")
async def admin_close_day_start(
    callback: CallbackQuery, settings: Settings, state: FSMContext
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_close_day)
    await callback.message.edit_text(
        "Введите дату для полного закрытия: <code>YYYY-MM-DD</code>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.waiting_close_day)
async def admin_close_day_save(message: Message, db: Database, state: FSMContext) -> None:
    close_date = message.text.strip()
    if not _is_valid_date(close_date):
        await message.answer("Неверный формат даты. Используйте YYYY-MM-DD.")
        return
    db.close_day(close_date)
    await state.clear()
    await message.answer("День закрыт.", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin_view_schedule")
async def admin_view_schedule_start(
    callback: CallbackQuery, settings: Settings, state: FSMContext, db: Database
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_view_schedule)
    today = date.today()
    month_later = today + timedelta(days=31)
    available_days = set(db.get_month_work_days(today.strftime("%Y-%m-%d"), month_later.strftime("%Y-%m-%d")))
    await callback.message.edit_text(
        "Выберите дату для просмотра расписания:",
        reply_markup=month_calendar_kb(available_days, month_offset=0),
    )
    await callback.answer()


@router.callback_query(AdminStates.waiting_view_schedule, F.data.startswith("pick_date:"))
async def admin_view_schedule_pick(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    date_str = callback.data.split(":")[1]
    schedule = db.get_schedule_by_date(date_str)
    if not schedule:
        await callback.message.edit_text(
            "На дату нет слотов.",
            reply_markup=admin_menu_kb(),
        )
        await state.clear()
        await callback.answer()
        return

    lines = [f"<b>Расписание на {format_ru_date(date_str)}</b>"]
    for row in schedule:
        if row["booking_id"]:
            lines.append(f"{row['time']} — занято ({row['name']}, {row['phone']})")
        else:
            lines.append(f"{row['time']} — свободно")

    await callback.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=admin_menu_kb())
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "admin_cancel_booking")
async def admin_cancel_booking_start(
    callback: CallbackQuery, settings: Settings, state: FSMContext
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_cancel_booking_date)
    await callback.message.edit_text(
        "Введите дату для отмены записи клиента: <code>YYYY-MM-DD</code>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.waiting_cancel_booking_date)
async def admin_cancel_booking_date(message: Message, db: Database, state: FSMContext) -> None:
    date_str = message.text.strip()
    if not _is_valid_date(date_str):
        await message.answer("Неверный формат даты. Используйте YYYY-MM-DD.")
        return
    bookings = db.get_bookings_for_date(date_str)
    if not bookings:
        await message.answer("На эту дату активных записей нет.", reply_markup=admin_menu_kb())
        await state.clear()
        return
    await state.clear()
    prepared = [
        {"id": row["id"], "name": row["name"], "time": row["time"]}
        for row in bookings
    ]
    await message.answer("Выберите запись для отмены:", reply_markup=bookings_manage_kb(date_str, prepared))


@router.callback_query(F.data.startswith("admin_cancel_by_id:"))
async def admin_cancel_by_id(
    callback: CallbackQuery,
    db: Database,
    settings: Settings,
    reminder_service: ReminderService,
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа", show_alert=True)
        return
    booking_id = int(callback.data.split(":")[1])
    booking = db.cancel_booking_by_id(booking_id)
    if booking is None:
        await callback.message.edit_text("Запись не найдена.", reply_markup=admin_menu_kb())
        await callback.answer()
        return

    reminder_service.cancel_reminder(booking["reminder_job_id"])
    await callback.message.edit_text("Запись отменена администратором.", reply_markup=admin_menu_kb())
    await callback.answer()
    await callback.bot.send_message(
        booking["user_id"],
        "<b>Ваша запись отменена администратором.</b>\n"
        f"Дата: <b>{format_ru_date(booking['date'])}</b>\n"
        f"Время: <b>{booking['time']}</b>",
        parse_mode="HTML",
    )
