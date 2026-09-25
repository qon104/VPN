from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    message: str


class StatusResponse(BaseModel):
    status: str
    detail: Optional[str] = None


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)