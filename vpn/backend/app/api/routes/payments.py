from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, verify_bot_secret
from app.config import get_settings
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentWebhook
from app.services.key_service import KeyService

router = APIRouter(prefix="/payments", tags=["Payments"])
settings = get_settings()


@router.post(
    "/webhook",
    summary="Вебхук от платёжной системы"
)
async def payment_webhook(
    payload: PaymentWebhook,
    db: AsyncSession = Depends(get_session),
    x_webhook_secret: str | None = Header(None, alias="X-Webhook-Secret"),
):
    """
    Сюда будет приходить уведомление об успешной оплате.
    Пока сделан универсальный вариант — потом подстроим под конкретного провайдера
    (Telegram Stars, CryptoBot, ЮKassa и т.д.).
    """
    # Простая проверка секрета (можно усилить)
    if settings.PAYMENT_WEBHOOK_SECRET and x_webhook_secret != settings.PAYMENT_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook secret"
        )

    if payload.status != "success":
        return {"status": "ignored", "reason": "not success"}

    if not payload.telegram_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="telegram_id is required"
        )

    # Здесь можно сохранить платёж в базу (PaymentCreate)
    # и сразу сгенерировать ключ.

    # Пока для примера просто возвращаем успех.
    # Реальную генерацию ключа лучше делать из бота после подтверждения оплаты,
    # либо прямо здесь.

    return {
        "status": "ok",
        "message": "Payment received"
    }


@router.post(
    "/create",
    response_model=PaymentResponse,
    summary="Создание записи о платеже (вызывается ботом)",
    dependencies=[Depends(verify_bot_secret)]
)
async def create_payment(
    payload: PaymentCreate,
    db: AsyncSession = Depends(get_session),
):
    # Пока заглушка — логику сохранения платежа добавим позже при необходимости
    return {
        "id": 0,
        "amount": payload.amount,
        "currency": payload.currency,
        "provider": payload.provider,
        "status": "pending",
        "created_at": "1970-01-01T00:00:00Z"
    }