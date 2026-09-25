from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_reply_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🛒 Купить"),
        KeyboardButton(text="📊 Подписка"),
    )
    builder.row(
        KeyboardButton(text="🔑 Ключ"),
        KeyboardButton(text="❓ Помощь"),
    )
    return builder.as_markup(resize_keyboard=True)
