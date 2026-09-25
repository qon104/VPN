from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import SubscriptionNotFoundError
from app.models.subscription import Subscription
from app.models.user import User


class SubscriptionService:

    @staticmethod
    async def get_active_subscription(
        db: AsyncSession,
        telegram_id: int,
    ) -> Optional[Subscription]:
        result = await db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return None

        now = datetime.now(timezone.utc)

        result = await db.execute(
            select(Subscription)
            .where(
                Subscription.user_id == user.id,
                Subscription.status == "active",
                Subscription.expires_at > now,
            )
            .order_by(Subscription.expires_at.desc())
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_subscription_by_id(
        db: AsyncSession,
        subscription_id: int,
    ) -> Subscription:
        result = await db.execute(
            select(Subscription)
            .options(selectinload(Subscription.user))
            .where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()
        if not subscription:
            raise SubscriptionNotFoundError()
        return subscription

    @staticmethod
    async def expire_old_subscriptions(db: AsyncSession) -> int:
        """
        Помечает просроченные подписки как expired.
        Возвращает количество обновлённых записей.
        Можно запускать по крону.
        """
        now = datetime.now(timezone.utc)

        result = await db.execute(
            select(Subscription).where(
                Subscription.status == "active",
                Subscription.expires_at <= now,
            )
        )
        subscriptions = result.scalars().all()

        count = 0
        for sub in subscriptions:
            sub.status = "expired"
            count += 1

        if count:
            await db.commit()

        return count