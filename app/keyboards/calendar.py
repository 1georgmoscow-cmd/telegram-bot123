import calendar
from datetime import date, datetime, timedelta

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def _month_add(base: date, offset: int) -> tuple[int, int]:
    month_index = (base.month - 1) + offset
    year = base.year + (month_index // 12)
    month = (month_index % 12) + 1
    return year, month


def month_calendar_kb(available_days: set[str], month_offset: int = 0) -> InlineKeyboardMarkup:
    today = date.today()
    month_later = today + timedelta(days=31)
    year, month = _month_add(today, month_offset)

    cal = calendar.Calendar(firstweekday=0)
    keyboard: list[list[InlineKeyboardButton]] = []
    keyboard.append(
        [InlineKeyboardButton(text=f"{calendar.month_name[month]} {year}", callback_data="ignore")]
    )
    keyboard.append([InlineKeyboardButton(text=day, callback_data="ignore") for day in WEEKDAYS])

    for week in cal.monthdatescalendar(year, month):
        row: list[InlineKeyboardButton] = []
        for day in week:
            day_str = day.strftime("%Y-%m-%d")
            is_in_range = today <= day <= month_later
            is_available = day_str in available_days

            if day.month != month or not is_in_range:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            elif is_available:
                row.append(
                    InlineKeyboardButton(text=str(day.day), callback_data=f"pick_date:{day_str}")
                )
            else:
                row.append(
                    InlineKeyboardButton(text=f"·{day.day}", callback_data="ignore")
                )
        keyboard.append(row)

    nav_row: list[InlineKeyboardButton] = []
    if month_offset > 0:
        nav_row.append(
            InlineKeyboardButton(text="◀️", callback_data=f"cal_month:{month_offset - 1}")
        )
    if month_offset < 1:
        nav_row.append(
            InlineKeyboardButton(text="▶️", callback_data=f"cal_month:{month_offset + 1}")
        )
    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([InlineKeyboardButton(text="В меню", callback_data="back_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def slots_kb(date_str: str, slots: list[str]) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=slot, callback_data=f"pick_time:{date_str}:{slot}")]
        for slot in slots
    ]
    keyboard.append([InlineKeyboardButton(text="Назад", callback_data="start_booking")])
    keyboard.append([InlineKeyboardButton(text="В меню", callback_data="back_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def confirm_booking_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подтвердить", callback_data="confirm_booking")],
            [InlineKeyboardButton(text="Отмена", callback_data="back_menu")],
        ]
    )


def format_ru_date(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%d.%m.%Y")
