import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.download_token import DownloadToken
from app.models.user import User

settings = get_settings()


class DownloadService:

    @staticmethod
    async def create_download_token(
        db: AsyncSession,
        telegram_id: int,
    ) -> str:
        result = await db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.DOWNLOAD_TOKEN_EXPIRE_HOURS
        )

        download_token = DownloadToken(
            token=token,
            user_id=user.id,
            expires_at=expires_at,
            used=False,
        )
        db.add(download_token)
        await db.commit()

        return token

    @staticmethod
    async def validate_and_use_token(
        db: AsyncSession,
        token: str,
    ) -> bool:
        result = await db.execute(
            select(DownloadToken).where(DownloadToken.token == token)
        )
        download_token = result.scalar_one_or_none()

        if not download_token:
            return False

        now = datetime.now(timezone.utc)

        if download_token.used:
            return False

        if download_token.expires_at < now:
            return False

        download_token.used = True
        await db.commit()
        return True