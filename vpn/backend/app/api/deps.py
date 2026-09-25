from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_db

settings = get_settings()


async def get_session() -> AsyncSession:
    async for session in get_db():
        yield session


async def verify_bot_secret(
    x_bot_secret: str = Header(..., alias="X-Bot-Secret")
) -> None:
    """
    Проверяет секретный заголовок, которым бот авторизуется в бэкенде.
    """
    if x_bot_secret != settings.BOT_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )