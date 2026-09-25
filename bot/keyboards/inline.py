from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.payment import PLANS


def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🛒 Купить подписку", callback_data="buy"),
    )
    builder.row(
        InlineKeyboardButton(text="📊 Моя подписка", callback_data="my_sub"),
        InlineKeyboardButton(text="🔑 Получить ключ", callback_data="get_key"),
    )
    builder.row(
        InlineKeyboardButton(text="❓ Помощь", callback_data="help"),
    )
    return builder.as_markup()


def plans_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for plan_id, plan in PLANS.items():
        text = f"{plan['title']} — {plan['price']} ⭐"
        builder.row(
            InlineKeyboardButton(text=text, callback_data=f"plan:{plan_id}")
        )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="back_to_menu")
    )
    return builder.as_markup()


def pay_kb(plan_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="💳 Оплатить Stars",
            callback_data=f"pay:{plan_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(text="« Выбрать другой тариф", callback_data="buy")
    )
    return builder.as_markup()


def after_payment_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔑 Получить ключ", callback_data="get_key"),
    )
    builder.row(
        InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_menu"),
    )
    return builder.as_markup()


def admin_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📈 Статистика", callback_data="admin:stats"),
    )
    builder.row(
        InlineKeyboardButton(text="🎁 Выдать себе доступ", callback_data="admin:grant_self"),
    )
    builder.row(
        InlineKeyboardButton(text="👤 Выдать доступ юзеру", callback_data="admin:grant_user"),
    )
    builder.row(
        InlineKeyboardButton(text="🔍 Инфо о юзере", callback_data="admin:user_info"),
    )
    builder.row(
        InlineKeyboardButton(text="🚫 Забанить", callback_data="admin:ban"),
        InlineKeyboardButton(text="✅ Разбанить", callback_data="admin:unban"),
    )
    builder.row(
        InlineKeyboardButton(text="❌ Снять подписку", callback_data="admin:revoke"),
    )
    builder.row(
        InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_menu"),
    )
    return builder.as_markup()


def admin_plans_kb(prefix: str) -> InlineKeyboardMarkup:
    """prefix = grant_self / grant_user_plan"""
    builder = InlineKeyboardBuilder()
    for plan_id, plan in PLANS.items():
        builder.row(
            InlineKeyboardButton(
                text=f"{plan['title']} ({plan['days']} дн.)",
                callback_data=f"admin:{prefix}:{plan_id}",
            )
        )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="admin:back")
    )
    return builder.as_markup()