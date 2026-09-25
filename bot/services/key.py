import aiohttp
from typing import Optional

from loader import settings
from services.user import user_service


class KeyService:
    """
    Запрос ключа у backend (Marzban / 3x-ui / свой API).
    Адаптируй под свой backend.
    """

    def __init__(self):
        self.base_url = settings.backend_url.rstrip("/")
        self.api_key = settings.backend_api_key

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                **kwargs,
            ) as resp:
                if resp.status >= 400:
                    text = await resp.text()
                    raise RuntimeError(f"Backend error {resp.status}: {text}")
                return await resp.json()

    async def create_or_get_key(
        self,
        user_id: int,
        username: Optional[str],
        days: int,
    ) -> dict:
        """
        Создаёт пользователя на backend и возвращает:
        {
            "key": "vless://....",
            "config_link": "https://..."
        }
        """
        # Пример под Marzban / кастомный API.
        # Замени path и payload под свой backend.
        payload = {
            "telegram_id": user_id,
            "username": username or f"user_{user_id}",
            "days": days,
            "protocol": "vless",
        }

        try:
            data = await self._request("POST", "/api/clients", json=payload)
            return {
                "key": data.get("subscription_url") or data.get("key") or data.get("link"),
                "config_link": data.get("config_link") or data.get("qr") or None,
            }
        except Exception:
            # Fallback: генерируем заглушку (для разработки без backend)
            return {
                "key": f"vless://{user_id}@vpn.example.com:443?security=reality&type=tcp#User_{user_id}",
                "config_link": f"https://vpn.example.com/sub/{user_id}",
            }

    async def issue_key_for_user(
        self,
        user_id: int,
        username: Optional[str],
        subscription_id: int,
        days: int,
    ) -> dict:
        """Создаёт ключ на backend и сохраняет в БД."""
        result = await self.create_or_get_key(user_id, username, days)
        await user_service.save_key(
            user_id=user_id,
            subscription_id=subscription_id,
            key_value=result["key"],
            config_link=result.get("config_link"),
        )
        return result


key_service = KeyService()
