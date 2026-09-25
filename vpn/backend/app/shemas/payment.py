from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema


class PaymentCreate(BaseModel):
    telegram_id: int
    amount: float = Field(..., gt=0)
    currency: str = "RUB"
    provider: str
    provider_payment_id: Optional[str] = None


class PaymentResponse(BaseSchema):
    id: int
    amount: float
    currency: str
    provider: str
    status: str
    created_at: datetime


class PaymentWebhook(BaseModel):
    """Схема под разные платёжки. Будем уточнять под конкретного провайдера."""
    provider: str
    payment_id: str
    status: str
    amount: Optional[float] = None
    telegram_id: Optional[int] = None
    raw: Optional[dict] = None