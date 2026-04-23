from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest


async def is_subscribed(bot: Bot, channel_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
    except TelegramBadRequest:
        return False
    return member.status in {"member", "administrator", "creator"}
