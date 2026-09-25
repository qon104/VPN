from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice
from aiogram.filters import Command

from keyboards.inline import plans_kb, pay_kb, after_payment_kb, main_menu_kb
from services.payment import PLANS, get_plan, build_invoice_prices, get_plan_days
from services.user import user_service
from services.key import key_service
from loader import settings

router = Router(name="buy")


@router.callback_query(F.data == "buy")
async def buy_callback(callback: CallbackQuery):
    text = (
        "🛒 <b>Выбери тариф</b>\n\n"
        "Оплата только через Telegram Stars ⭐"
    )
    await callback.message.edit_text(text, reply_markup=plans_kb())
    await callback.answer()


@router.message(F.text == "🛒 Купить")
async def buy_message(message: Message):
    text = (
        "🛒 <b>Выбери тариф</b>\n\n"
        "Оплата только через Telegram Stars ⭐"
    )
    await message.answer(text, reply_markup=plans_kb())


@router.callback_query(F.data.startswith("plan:"))
async def choose_plan(callback: CallbackQuery):
    plan_id = callback.data.split(":")[1]
    plan = get_plan(plan_id)
    if not plan:
        await callback.answer("Тариф не найден", show_alert=True)
        return

    text = (
        f"📦 <b>{plan['title']}</b>\n\n"
        f"{plan['description']}\n"
        f"💰 Цена: <b>{plan['price']} ⭐</b>\n\n"
        "Нажми кнопку ниже, чтобы оплатить."
    )
    await callback.message.edit_text(text, reply_markup=pay_kb(plan_id))
    await callback.answer()


@router.callback_query(F.data.startswith("pay:"))
async def send_invoice(callback: CallbackQuery, bot: Bot):
    plan_id = callback.data.split(":")[1]
    plan = get_plan(plan_id)
    if not plan:
        await callback.answer("Тариф не найден", show_alert=True)
        return

    prices = build_invoice_prices(plan_id)

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"VPN — {plan['title']}",
        description=plan["description"],
        payload=f"vpn_{plan_id}_{callback.from_user.id}",
        currency="XTR",  # Telegram Stars
        prices=prices,
        provider_token="",  # для Stars оставляем пустым
    )
    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payment = message.successful_payment
    payload = payment.invoice_payload  # vpn_1m_123456

    try:
        _, plan_id, user_id_str = payload.split("_")
        user_id = int(user_id_str)
    except Exception:
        await message.answer("❌ Ошибка обработки платежа. Напиши админу.")
        return

    if user_id != message.from_user.id:
        await message.answer("❌ Ошибка: платёж не принадлежит тебе.")
        return

    plan = get_plan(plan_id)
    if not plan:
        await message.answer("❌ Неизвестный тариф.")
        return

    days = plan["days"]
    sub_id = await user_service.create_subscription(
        user_id=user_id,
        plan=plan_id,
        days=days,
        payment_id=payment.telegram_payment_charge_id,
    )

    # Сразу выдаём ключ
    try:
        key_data = await key_service.issue_key_for_user(
            user_id=user_id,
            username=message.from_user.username,
            subscription_id=sub_id,
            days=days,
        )
        key_text = (
            f"✅ <b>Оплата прошла успешно!</b>\n\n"
            f"Тариф: <b>{plan['title']}</b>\n"
            f"Срок: <b>{days} дней</b>\n\n"
            f"🔑 <b>Твой ключ:</b>\n"
            f"<code>{key_data['key']}</code>\n"
        )
        if key_data.get("config_link"):
            key_text += f"\n📎 Ссылка на конфиг:\n{key_data['config_link']}"

        key_text += "\n\nИмпортируй ключ в клиент (v2rayNG / Streisand / Hiddify)."
        await message.answer(key_text, reply_markup=after_payment_kb())
    except Exception as e:
        await message.answer(
            f"✅ Оплата прошла, но не удалось выдать ключ автоматически.\n"
            f"Нажми «Получить ключ» или напиши админу.\n\n"
            f"Ошибка: <code>{e}</code>",
            reply_markup=after_payment_kb(),
        )
