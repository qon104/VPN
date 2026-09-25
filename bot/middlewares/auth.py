from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from services.user import user_service


class AuthMiddleware(BaseMiddleware):
    """Регистрирует пользователя и проверяет бан."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        if user:
            await user_service.ensure_user(
                user_id=user.id,
                username=user.username,
                full_name=user.full_name or "",
            )
            if await user_service.is_banned(user.id):
                # Можно отправить сообщение, но проще просто игнорировать
                return None
        return await handler(event, data)
