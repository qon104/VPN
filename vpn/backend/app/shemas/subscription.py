from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema


class SubscriptionResponse(BaseSchema):
    id: int
    plan: str
    status: str
    started_at: datetime
    expires_at: datetime
    days_left: Optional[int] = None


class SubscriptionCreate(BaseModel):
    telegram_id: int
    plan: str = Field(..., pattern="^(month|3month|year)$")
    days: int = Field(..., gt=0)