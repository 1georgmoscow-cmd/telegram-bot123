from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.keyboards.common import back_to_menu_kb, portfolio_kb

router = Router()


@router.callback_query(F.data == "prices")
async def show_prices(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "<b>Прайс</b>\n\n"
        "Френч — <b>1000₽</b>\n"
        "Квадрат — <b>500₽</b>",
        parse_mode="HTML",
        reply_markup=back_to_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "portfolio")
async def show_portfolio(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "<b>Портфолио</b>\nНажмите кнопку ниже:",
        parse_mode="HTML",
        reply_markup=portfolio_kb(),
    )
    await callback.answer()
