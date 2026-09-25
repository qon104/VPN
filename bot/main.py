import asyncio
import logging

from aiogram import Dispatcher

from loader import bot, dp, settings
from middlewares.auth import AuthMiddleware
from services.user import user_service

# Handlers
from handlers import start, buy, my_subscription, download, admin


async def on_startup():
    await user_service.init_db()
    logging.info("Database initialized")
    logging.info(f"Bot started. Admins: {settings.admin_ids}")


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Middleware
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Routers
    dp.include_router(start.router)
    dp.include_router(buy.router)
    dp.include_router(my_subscription.router)
    dp.include_router(download.router)
    dp.include_router(admin.router)

    await on_startup()

    # Удаляем вебхук на всякий случай и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
