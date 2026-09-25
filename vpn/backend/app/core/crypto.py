import hmac
import hashlib
import secrets
import string
from datetime import datetime, timezone

from app.config import get_settings

settings = get_settings()


def _generate_raw_key(length: int = 25) -> str:
    """Генерирует читаемый ключ вида XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"""
    alphabet = string.ascii_uppercase + string.digits
    chars = [secrets.choice(alphabet) for _ in range(length)]
    # Разбиваем на блоки по 5
    parts = ["".join(chars[i:i+5]) for i in range(0, length, 5)]
    return "-".join(parts)


def generate_signed_key() -> tuple[str, str]:
    """
    Возвращает (полный_ключ, prefix).
    Ключ подписывается HMAC, чтобы нельзя было подделать.
    """
    raw = _generate_raw_key(25)
    signature = hmac.new(
        settings.KEY_HMAC_SECRET.encode("utf-8"),
        raw.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()[:8].upper()

    full_key = f"{raw}-{signature}"
    prefix = full_key[:8]
    return full_key, prefix


def verify_signed_key(key: str) -> bool:
    """Проверяет, что ключ имеет правильную подпись."""
    try:
        parts = key.rsplit("-", 1)
        if len(parts) != 2:
            return False
        raw, signature = parts
        expected = hmac.new(
            settings.KEY_HMAC_SECRET.encode("utf-8"),
            raw.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()[:8].upper()
        return hmac.compare_digest(signature, expected)
    except Exception:
        return False