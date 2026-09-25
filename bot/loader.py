from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(..., alias="BOT_TOKEN")
    admin_ids: list[int] = Field(default_factory=list, alias="ADMIN_IDS")
    backend_url: str = Field("https://example.com", alias="BACKEND_URL")
    backend_api_key: str = Field("changeme", alias="BACKEND_API_KEY")
    db_path: str = Field("bot.db", alias="DB_PATH")

    price_1_month: int = Field(150, alias="PRICE_1_MONTH")
    price_3_months: int = Field(400, alias="PRICE_3_MONTHS")
    price_6_months: int = Field(700, alias="PRICE_6_MONTHS")
    price_12_months: int = Field(1200, alias="PRICE_12_MONTHS")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        if isinstance(v, int):
            return [v]
        return v or []


settings = Settings()

bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=MemoryStorage())
