from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from app.config import Settings
from app.database.db import Database
from app.handlers.booking import _show_calendar
from app.keyboards.common import subscription_kb
from app.services.subscription import is_subscribed

router = Router()


@router.callback_query(F.data == "check_subscription")
async def check_subscription(
    callback: CallbackQuery, bot: Bot, settings: Settings, db: Database
) -> None:
    subscribed = await is_subscribed(bot, settings.channel_id, callback.from_user.id)
    if not subscribed:
        await callback.message.edit_text(
            "Для записи необходимо подписаться на канал",
            reply_markup=subscription_kb(settings.channel_link),
        )
        await callback.answer("Подписка не найдена", show_alert=True)
        return

    await _show_calendar(callback, db, month_offset=0)
    await callback.answer("Подписка подтверждена ✅")
