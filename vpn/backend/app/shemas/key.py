from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema


class KeyActivateRequest(BaseModel):
    key: str = Field(..., min_length=20, max_length=64)
    device_id: Optional[str] = Field(None, max_length=128)


class KeyActivateResponse(BaseSchema):
    status: str
    expires_at: datetime
    plan: str
    message: str = "Ключ успешно активирован"


class KeyStatusResponse(BaseSchema):
    status: str                    # active / expired / revoked / not_found
    expires_at: Optional[datetime] = None
    plan: Optional[str] = None
    days_left: Optional[int] = None


class KeyGenerateRequest(BaseModel):
    telegram_id: int
    plan: str = Field(..., pattern="^(month|3month|year)$")
    days: int = Field(..., gt=0)


class KeyGenerateResponse(BaseSchema):
    key: str
    expires_at: datetime
    plan: str
    subscription_id: int