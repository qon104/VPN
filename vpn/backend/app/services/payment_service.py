from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.models.user import User
from app.services.key_service import KeyService


class PaymentService:

    @staticmethod
    async def create_payment(
        db: AsyncSession,
        telegram_id: int,
        amount: float,
        currency: str,
        provider: str,
        provider_payment_id: Optional[str] = None,
    ) -> Payment:
        result = await db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=telegram_id)
            db.add(user)
            await db.flush()

        payment = Payment(
            user_id=user.id,
            amount=amount,
            currency=currency,
            provider=provider,
            provider_payment_id=provider_payment_id,
            status="pending",
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return payment

    @staticmethod
    async def mark_payment_success(
        db: AsyncSession,
        provider_payment_id: str,
        plan: str = "month",
        days: int = 30,
    ) -> Optional[tuple[str, Payment]]:
        """
        Помечает платёж успешным и генерирует ключ.
        Возвращает (ключ, payment) или None.
        """
        result = await db.execute(
            select(Payment).where(Payment.provider_payment_id == provider_payment_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            return None

        if payment.status == "success":
            return None  # уже обработан

        payment.status = "success"
        await db.flush()

        # Получаем telegram_id пользователя
        result = await db.execute(
            select(User).where(User.id == payment.user_id)
        )
        user = result.scalar_one()

        full_key, key_obj, subscription = await KeyService.generate_key(
            db=db,
            telegram_id=user.telegram_id,
            plan=plan,
            days=days,
        )

        await db.commit()
        return full_key, payment