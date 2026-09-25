from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from keyboards.inline import main_menu_kb, plans_kb
from services.user import user_service
from services.payment import PLANS

router = Router(name="my_subscription")


def _format_sub(sub: dict) -> str:
    plan_id = sub["plan"]
    plan_name = PLANS.get(plan_id, {}).get("title", plan_id)
    expires = datetime.fromisoformat(sub["expires_at"])
    now = datetime.utcnow()
    left = expires - now
    days_left = max(0, left.days)

    return (
        f"📊 <b>Твоя подписка</b>\n\n"
        f"Тариф: <b>{plan_name}</b>\n"
        f"Активна до: <b>{expires.strftime('%d.%m.%Y %H:%M')} UTC</b>\n"
        f"Осталось: <b>{days_left} дн.</b>\n"
    )


@router.callback_query(F.data == "my_sub")
async def my_sub_callback(callback: CallbackQuery):
    sub = await user_service.get_active_subscription(callback.from_user.id)
    if not sub:
        text = (
            "📊 У тебя нет активной подписки.\n\n"
            "Нажми «Купить подписку», чтобы начать."
        )
        await callback.message.edit_text(text, reply_markup=plans_kb())
    else:
        text = _format_sub(sub)
        await callback.message.edit_text(text, reply_markup=main_menu_kb())
    await callback.answer()


@router.message(F.text == "📊 Подписка")
async def my_sub_message(message: Message):
    sub = await user_service.get_active_subscription(message.from_user.id)
    if not sub:
        text = (
            "📊 У тебя нет активной подписки.\n\n"
            "Нажми «Купить подписку», чтобы начать."
        )
        await message.answer(text, reply_markup=plans_kb())
    else:
        text = _format_sub(sub)
        await message.answer(text, reply_markup=main_menu_kb())
