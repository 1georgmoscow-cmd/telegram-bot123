from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить рабочий день", callback_data="admin_add_day")],
            [InlineKeyboardButton(text="Добавить слот", callback_data="admin_add_slot")],
            [InlineKeyboardButton(text="Удалить слот", callback_data="admin_delete_slot")],
            [InlineKeyboardButton(text="Отменить запись клиента", callback_data="admin_cancel_booking")],
            [InlineKeyboardButton(text="Закрыть день", callback_data="admin_close_day")],
            [InlineKeyboardButton(text="Посмотреть расписание", callback_data="admin_view_schedule")],
            [InlineKeyboardButton(text="В меню", callback_data="back_menu")],
        ]
    )


def slots_manage_kb(prefix: str, date: str, slots: list[str]) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=slot, callback_data=f"{prefix}:{date}:{slot}")]
        for slot in slots
    ]
    keyboard.append([InlineKeyboardButton(text="В админ-меню", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def bookings_manage_kb(date: str, bookings: list[dict]) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"{item['time']} — {item['name']}",
                callback_data=f"admin_cancel_by_id:{item['id']}",
            )
        ]
        for item in bookings
    ]
    keyboard.append([InlineKeyboardButton(text="В админ-меню", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
