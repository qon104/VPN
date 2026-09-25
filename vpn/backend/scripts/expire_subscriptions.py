"""
Скрипт для автоматического протухания подписок.
Можно запускать по крону раз в час/день.
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db.session import AsyncSessionLocal
from app.services.subscription_service import SubscriptionService


async def main():
    async with AsyncSessionLocal() as db:
        count = await SubscriptionService.expire_old_subscriptions(db)
        print(f"Expired subscriptions: {count}")


if __name__ == "__main__":
    asyncio.run(main())