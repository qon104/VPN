from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from keyboards.inline import main_menu_kb
from keyboards.reply import main_reply_kb

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        "Это бот для покупки VPN-подписки.\n\n"
        "• Быстрый и стабильный доступ\n"
        "• Оплата через Telegram Stars\n"
        "• Ключ выдаётся мгновенно после оплаты\n\n"
        "Выбери действие:"
    )
    await message.answer(text, reply_markup=main_menu_kb())
    await message.answer("Или используй кнопки ниже 👇", reply_markup=main_reply_kb())


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏠 Главное меню\n\nВыбери действие:",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    text = (
        "❓ <b>Помощь</b>\n\n"
        "1. Нажми «Купить подписку» и выбери тариф\n"
        "2. Оплати через Telegram Stars\n"
        "3. После оплаты нажми «Получить ключ»\n"
        "4. Импортируй ключ в клиент (v2rayNG, Streisand, Hiddify и т.д.)\n\n"
        "По вопросам пиши администратору."
    )
    await callback.message.edit_text(text, reply_markup=main_menu_kb())
    await callback.answer()


@router.message(F.text == "❓ Помощь")
async def help_message(message: Message):
    text = (
        "❓ <b>Помощь</b>\n\n"
        "1. Нажми «Купить подписку» и выбери тариф\n"
        "2. Оплати через Telegram Stars\n"
        "3. После оплаты нажми «Получить ключ»\n"
        "4. Импортируй ключ в клиент (v2rayNG, Streisand, Hiddify и т.д.)\n\n"
        "По вопросам пиши администратору."
    )
    await message.answer(text, reply_markup=main_menu_kb())
