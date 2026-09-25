from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from keyboards.inline import main_menu_kb, plans_kb, after_payment_kb
from services.user import user_service
from services.key import key_service
from services.payment import get_plan

router = Router(name="download")


@router.callback_query(F.data == "get_key")
async def get_key_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    sub = await user_service.get_active_subscription(user_id)

    if not sub:
        await callback.message.edit_text(
            "❌ У тебя нет активной подписки.\nСначала купи тариф.",
            reply_markup=plans_kb(),
        )
        await callback.answer()
        return

    key_data = await user_service.get_user_key(user_id)

    if not key_data:
        # Пробуем выдать заново
        try:
            plan = get_plan(sub["plan"])
            days = plan["days"] if plan else 30
            key_data = await key_service.issue_key_for_user(
                user_id=user_id,
                username=callback.from_user.username,
                subscription_id=sub["id"],
                days=days,
            )
            key_value = key_data["key"]
            config_link = key_data.get("config_link")
        except Exception as e:
            await callback.message.edit_text(
                f"❌ Не удалось получить ключ.\nОшибка: <code>{e}</code>\n"
                "Напиши администратору.",
                reply_markup=main_menu_kb(),
            )
            await callback.answer()
            return
    else:
        key_value = key_data["key_value"]
        config_link = key_data.get("config_link")

    text = (
        "🔑 <b>Твой VPN-ключ</b>\n\n"
        f"<code>{key_value}</code>\n"
    )
    if config_link:
        text += f"\n📎 Ссылка:\n{config_link}\n"

    text += (
        "\n📱 <b>Как использовать:</b>\n"
        "1. Скачай клиент (v2rayNG / Streisand / Hiddify / Nekobox)\n"
        "2. Импортируй ключ из буфера\n"
        "3. Подключайся\n"
    )

    await callback.message.edit_text(text, reply_markup=main_menu_kb())
    await callback.answer()


@router.message(F.text == "🔑 Ключ")
async def get_key_message(message: Message):
    user_id = message.from_user.id
    sub = await user_service.get_active_subscription(user_id)

    if not sub:
        await message.answer(
            "❌ У тебя нет активной подписки.\nСначала купи тариф.",
            reply_markup=plans_kb(),
        )
        return

    key_data = await user_service.get_user_key(user_id)

    if not key_data:
        try:
            plan = get_plan(sub["plan"])
            days = plan["days"] if plan else 30
            result = await key_service.issue_key_for_user(
                user_id=user_id,
                username=message.from_user.username,
                subscription_id=sub["id"],
                days=days,
            )
            key_value = result["key"]
            config_link = result.get("config_link")
        except Exception as e:
            await message.answer(
                f"❌ Не удалось получить ключ.\nОшибка: <code>{e}</code>\n"
                "Напиши администратору.",
                reply_markup=main_menu_kb(),
            )
            return
    else:
        key_value = key_data["key_value"]
        config_link = key_data.get("config_link")

    text = (
        "🔑 <b>Твой VPN-ключ</b>\n\n"
        f"<code>{key_value}</code>\n"
    )
    if config_link:
        text += f"\n📎 Ссылка:\n{config_link}\n"

    text += (
        "\n📱 <b>Как использовать:</b>\n"
        "1. Скачай клиент (v2rayNG / Streisand / Hiddify / Nekobox)\n"
        "2. Импортируй ключ из буфера\n"
        "3. Подключайся\n"
    )

    await message.answer(text, reply_markup=main_menu_kb())
