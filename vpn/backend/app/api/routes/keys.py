from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, verify_bot_secret
from app.schemas.key import (
    KeyActivateRequest,
    KeyActivateResponse,
    KeyGenerateRequest,
    KeyGenerateResponse,
    KeyStatusResponse,
)
from app.services.key_service import KeyService

router = APIRouter(prefix="/keys", tags=["Keys"])


@router.post(
    "/activate",
    response_model=KeyActivateResponse,
    summary="Активация ключа (вызывается из приложения)"
)
async def activate_key(
    payload: KeyActivateRequest,
    db: AsyncSession = Depends(get_session),
):
    key = await KeyService.activate_key(
        db=db,
        key_str=payload.key,
        device_id=payload.device_id,
    )

    return KeyActivateResponse(
        status="activated",
        expires_at=key.expires_at,
        plan=key.subscription.plan,
        message="Ключ успешно активирован"
    )


@router.get(
    "/status",
    response_model=KeyStatusResponse,
    summary="Проверка статуса ключа (вызывается из приложения)"
)
async def get_key_status(
    key: str,
    db: AsyncSession = Depends(get_session),
):
    status_data = await KeyService.get_key_status(db=db, key_str=key)
    return KeyStatusResponse(**status_data)


@router.post(
    "/generate",
    response_model=KeyGenerateResponse,
    summary="Генерация ключа (вызывается только ботом)",
    dependencies=[Depends(verify_bot_secret)]
)
async def generate_key(
    payload: KeyGenerateRequest,
    db: AsyncSession = Depends(get_session),
):
    full_key, key_obj, subscription = await KeyService.generate_key(
        db=db,
        telegram_id=payload.telegram_id,
        plan=payload.plan,
        days=payload.days,
    )

    return KeyGenerateResponse(
        key=full_key,
        expires_at=key_obj.expires_at,
        plan=subscription.plan,
        subscription_id=subscription.id,
    )