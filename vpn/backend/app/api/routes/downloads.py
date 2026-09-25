from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, verify_bot_secret
from app.config import get_settings
from app.services.download_service import DownloadService

router = APIRouter(prefix="/downloads", tags=["Downloads"])
settings = get_settings()


@router.post(
    "/create-token",
    summary="Создать одноразовую ссылку на скачивание (бот)",
    dependencies=[Depends(verify_bot_secret)]
)
async def create_download_token(
    telegram_id: int,
    db: AsyncSession = Depends(get_session),
):
    token = await DownloadService.create_download_token(db, telegram_id)
    download_url = f"{settings.DOWNLOAD_BASE_URL}/{token}"
    return {
        "token": token,
        "download_url": download_url
    }


@router.get(
    "/{token}",
    summary="Скачивание файла по одноразовому токену"
)
async def download_file(
    token: str,
    db: AsyncSession = Depends(get_session),
):
    is_valid = await DownloadService.validate_and_use_token(db, token)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ссылка недействительна или уже использована"
        )

    # Здесь должна быть реальная ссылка на файл приложения
    # Пока делаем редирект-заглушку
    file_url = "https://your-storage.com/app/latest/VPNBrowserSetup.exe"
    return RedirectResponse(url=file_url)