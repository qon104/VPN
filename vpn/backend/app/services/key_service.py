from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.crypto import generate_signed_key, verify_signed_key
from app.core.exceptions import (
    InvalidKeyError,
    KeyAlreadyActivatedError,
    KeyExpiredError,
    KeyNotFoundError,
    KeyRevokedError,
)
from app.core.security import hash_key
from app.models.key import Key
from app.models.subscription import Subscription
from app.models.user import User


class KeyService:

    @staticmethod
    async def get_or_create_user(db: AsyncSession, telegram_id: int) -> User:
        result = await db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user:
            return user

        user = User(telegram_id=telegram_id)
        db.add(user)
        await db.flush()
        return user

    @staticmethod
    async def generate_key(
        db: AsyncSession,
        telegram_id: int,
        plan: str,
        days: int,
    ) -> tuple[str, Key, Subscription]:
        """
        Генерирует новый ключ + создаёт подписку.
        Возвращает: (полный_ключ, объект Key, объект Subscription)
        """
        user = await KeyService.get_or_create_user(db, telegram_id)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=days)

        # Создаём подписку
        subscription = Subscription(
            user_id=user.id,
            plan=plan,
            status="active",
            started_at=now,
            expires_at=expires_at,
        )
        db.add(subscription)
        await db.flush()

        # Генерируем ключ
        full_key, prefix = generate_signed_key()
        key_hash = hash_key(full_key)

        key = Key(
            key_hash=key_hash,
            key_prefix=prefix,
            user_id=user.id,
            subscription_id=subscription.id,
            status="issued",
            expires_at=expires_at,
        )
        db.add(key)
        await db.commit()

        # Обновляем объекты
        await db.refresh(key)
        await db.refresh(subscription)

        return full_key, key, subscription

    @staticmethod
    async def activate_key(
        db: AsyncSession,
        key_str: str,
        device_id: Optional[str] = None,
    ) -> Key:
        if not verify_signed_key(key_str):
            raise InvalidKeyError()

        key_hash = hash_key(key_str)

        result = await db.execute(
            select(Key)
            .options(selectinload(Key.subscription))
            .where(Key.key_hash == key_hash)
        )
        key = result.scalar_one_or_none()

        if not key:
            raise KeyNotFoundError()

        if key.status == "activated":
            raise KeyAlreadyActivatedError()

        if key.status == "revoked":
            raise KeyRevokedError()

        now = datetime.now(timezone.utc)
        if key.expires_at < now:
            key.status = "expired"
            await db.commit()
            raise KeyExpiredError()

        # Активируем
        key.status = "activated"
        key.activated_at = now
        key.activated_device_id = device_id

        await db.commit()
        await db.refresh(key)
        return key

    @staticmethod
    async def get_key_status(
        db: AsyncSession,
        key_str: str,
    ) -> dict:
        if not verify_signed_key(key_str):
            return {
                "status": "not_found",
                "expires_at": None,
                "plan": None,
                "days_left": None,
            }

        key_hash = hash_key(key_str)

        result = await db.execute(
            select(Key)
            .options(selectinload(Key.subscription))
            .where(Key.key_hash == key_hash)
        )
        key = result.scalar_one_or_none()

        if not key:
            return {
                "status": "not_found",
                "expires_at": None,
                "plan": None,
                "days_left": None,
            }

        now = datetime.now(timezone.utc)

        if key.status == "revoked":
            status = "revoked"
        elif key.expires_at < now:
            status = "expired"
            if key.status != "expired":
                key.status = "expired"
                await db.commit()
        elif key.status == "activated":
            status = "active"
        else:
            status = key.status  # issued

        days_left = max(0, (key.expires_at - now).days)

        return {
            "status": status,
            "expires_at": key.expires_at,
            "plan": key.subscription.plan if key.subscription else None,
            "days_left": days_left,
        }