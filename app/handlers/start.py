from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.keyboards.common import main_menu_kb

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message, settings: Settings) -> None:
    is_admin = message.from_user.id == settings.admin_id
    await message.answer(
        "<b>Добро пожаловать!</b>\nВыберите действие в меню ниже:",
        parse_mode="HTML",
        reply_markup=main_menu_kb(is_admin=is_admin),
    )


@router.callback_query(F.data == "back_menu")
async def back_menu(callback: CallbackQuery, settings: Settings) -> None:
    is_admin = callback.from_user.id == settings.admin_id
    await callback.message.edit_text(
        "<b>Главное меню</b>\nВыберите нужный раздел:",
        parse_mode="HTML",
        reply_markup=main_menu_kb(is_admin=is_admin),
    )
    await callback.answer()


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery) -> None:
    await callback.answer()
