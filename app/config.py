import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class Settings:
    bot_token: str
    admin_id: int
    channel_id: int
    channel_link: str
    database_path: str = "app.db"
    timezone: str = "Europe/Moscow"


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    admin_id_raw = os.getenv("ADMIN_ID", "").strip()
    channel_id_raw = os.getenv("CHANNEL_ID", "").strip()
    channel_link = os.getenv("CHANNEL_LINK", "").strip()
    db_path = os.getenv("DB_PATH", "app.db").strip()
    timezone = os.getenv("TIMEZONE", "Europe/Moscow").strip()

    if not token:
        raise ValueError("BOT_TOKEN is not set")
    if not admin_id_raw:
        raise ValueError("ADMIN_ID is not set")
    if not channel_id_raw:
        raise ValueError("CHANNEL_ID is not set")
    if not channel_link:
        raise ValueError("CHANNEL_LINK is not set")

    return Settings(
        bot_token=token,
        admin_id=int(admin_id_raw),
        channel_id=int(channel_id_raw),
        channel_link=channel_link,
        database_path=db_path,
        timezone=timezone,
    )
