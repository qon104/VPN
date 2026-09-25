from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from loader import settings
from keyboards.inline import admin_kb, admin_plans_kb, main_menu_kb
from services.user import user_service
from services.key import key_service
from services.payment import get_plan, PLANS

router = Router(name="admin")


class AdminStates(StatesGroup):
    waiting_ban_id = State()
    waiting_unban_id = State()
    waiting_grant_user_id = State()
    waiting_user_info_id = State()
    waiting_revoke_id = State()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


async def _grant_access(target_user_id: int, plan_id: str, username: str | None = None) -> dict:
    """Выдаёт подписку + ключ без оплаты."""
    plan = get_plan(plan_id)
    if not plan:
        raise ValueError("Неизвестный тариф")

    days = plan["days"]
    sub_id = await user_service.create_subscription(
        user_id=target_user_id,
        plan=plan_id,
        days=days,
        payment_id="admin_grant",
    )
    key_data = await key_service.issue_key_for_user(
        user_id=target_user_id,
        username=username,
        subscription_id=sub_id,
        days=days,
    )
    return {
        "plan": plan,
        "days": days,
        "key": key_data.get("key") or key_data.get("key_value"),
        "config_link": key_data.get("config_link"),
    }


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "🛠 <b>Админ-панель</b>\n\nТолько для администраторов.",
        reply_markup=admin_kb(),
    )


@router.callback_query(F.data == "admin:back")
async def admin_back(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(
        "🛠 <b>Админ-панель</b>",
        reply_markup=admin_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    users = await user_service.count_users()
    active = await user_service.count_active_subs()

    text = (
        "📈 <b>Статистика</b>\n\n"
        f"👥 Всего пользователей: <b>{users}</b>\n"
        f"✅ Активных подписок: <b>{active}</b>\n"
    )
    await callback.message.edit_text(text, reply_markup=admin_kb())
    await callback.answer()


@router.callback_query(F.data == "admin:grant_self")
async def admin_grant_self_choose(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(
        "🎁 <b>Выдать себе доступ</b>\n\nВыбери тариф:",
        reply_markup=admin_plans_kb("grant_self"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:grant_self:"))
async def admin_grant_self_do(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    plan_id = callback.data.split(":")[-1]
    try:
        result = await _grant_access(
            target_user_id=callback.from_user.id,
            plan_id=plan_id,
            username=callback.from_user.username,
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка: <code>{e}</code>",
            reply_markup=admin_kb(),
        )
        await callback.answer()
        return

    text = (
        f"✅ <b>Тебе выдан доступ</b>\n\n"
        f"Тариф: <b>{result['plan']['title']}</b>\n"
        f"Срок: <b>{result['days']} дн.</b>\n\n"
        f"🔑 Ключ:\n<code>{result['key']}</code>\n"
    )
    if result.get("config_link"):
        text += f"\n📎 {result['config_link']}"

    await callback.message.edit_text(text, reply_markup=admin_kb())
    await callback.answer("Готово!")


@router.callback_query(F.data == "admin:grant_user")
async def admin_grant_user_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_grant_user_id)
    await callback.message.edit_text(
        "👤 Отправь <b>Telegram ID</b> пользователя,\n"
        "которому выдать доступ:\n\n"
        "(или /cancel для отмены)",
    )
    await callback.answer()


@router.message(AdminStates.waiting_grant_user_id)
async def admin_grant_user_got_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text and message.text.strip().lower() in ("/cancel", "cancel"):
        await state.clear()
        await message.answer("Отменено.", reply_markup=admin_kb())
        return
    try:
        target_id = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("Нужен числовой ID. Попробуй ещё раз или /cancel")
        return

    await state.update_data(grant_target_id=target_id)
    await state.set_state(None)
    await message.answer(
        f"ID: <code>{target_id}</code>\nВыбери тариф:",
        reply_markup=admin_plans_kb("grant_user_plan"),
    )


@router.callback_query(F.data.startswith("admin:grant_user_plan:"))
async def admin_grant_user_do(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    data = await state.get_data()
    target_id = data.get("grant_target_id")
    if not target_id:
        await callback.message.edit_text(
            "❌ Сначала укажи ID пользователя.",
            reply_markup=admin_kb(),
        )
        await callback.answer()
        return

    plan_id = callback.data.split(":")[-1]
    try:
        await user_service.ensure_user(target_id, None, f"user_{target_id}")
        result = await _grant_access(
            target_user_id=target_id,
            plan_id=plan_id,
            username=None,
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка: <code>{e}</code>",
            reply_markup=admin_kb(),
        )
        await callback.answer()
        return

    await state.clear()
    text = (
        f"✅ Доступ выдан пользователю <code>{target_id}</code>\n\n"
        f"Тариф: <b>{result['plan']['title']}</b>\n"
        f"Срок: <b>{result['days']} дн.</b>\n\n"
        f"🔑 Ключ:\n<code>{result['key']}</code>\n"
    )
    if result.get("config_link"):
        text += f"\n📎 {result['config_link']}"

    await callback.message.edit_text(text, reply_markup=admin_kb())
    await callback.answer("Готово!")


@router.callback_query(F.data == "admin:user_info")
async def admin_user_info_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_user_info_id)
    await callback.message.edit_text(
        "🔍 Отправь <b>Telegram ID</b> пользователя:\n\n(/cancel — отмена)"
    )
    await callback.answer()


@router.message(AdminStates.waiting_user_info_id)
async def admin_user_info_do(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text and message.text.strip().lower() in ("/cancel", "cancel"):
        await state.clear()
        await message.answer("Отменено.", reply_markup=admin_kb())
        return
    try:
        target_id = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("Нужен числовой ID.")
        return

    await state.clear()
    sub = await user_service.get_active_subscription(target_id)
    banned = await user_service.is_banned(target_id)
    key_data = await user_service.get_user_key(target_id)

    text = f"👤 <b>Юзер</b> <code>{target_id}</code>\n\n"
    text += f"Бан: <b>{'да 🚫' if banned else 'нет'}</b>\n"

    if sub:
        plan_name = PLANS.get(sub["plan"], {}).get("title", sub["plan"])
        expires = datetime.fromisoformat(sub["expires_at"])
        text += (
            f"Подписка: <b>{plan_name}</b>\n"
            f"До: <b>{expires.strftime('%d.%m.%Y %H:%M')} UTC</b>\n"
        )
    else:
        text += "Подписка: <b>нет</b>\n"

    if key_data:
        text += f"\n🔑 Ключ:\n<code>{key_data['key_value']}</code>\n"
        if key_data.get("config_link"):
            text += f"📎 {key_data['config_link']}\n"
    else:
        text += "\nКлюч: нет\n"

    await message.answer(text, reply_markup=admin_kb())


@router.callback_query(F.data == "admin:ban")
async def admin_ban_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_ban_id)
    await callback.message.edit_text(
        "🚫 Отправь Telegram ID для бана:\n\n(/cancel — отмена)"
    )
    await callback.answer()


@router.callback_query(F.data == "admin:unban")
async def admin_unban_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_unban_id)
    await callback.message.edit_text(
        "✅ Отправь Telegram ID для разбана:\n\n(/cancel — отмена)"
    )
    await callback.answer()


@router.message(AdminStates.waiting_ban_id)
async def process_ban(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text and message.text.strip().lower() in ("/cancel", "cancel"):
        await state.clear()
        await message.answer("Отменено.", reply_markup=admin_kb())
        return
    try:
        user_id = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("Нужен числовой ID.")
        return

    await user_service.ensure_user(user_id, None, f"user_{user_id}")
    await user_service.set_ban(user_id, True)
    await state.clear()
    await message.answer(f"✅ <code>{user_id}</code> забанен.", reply_markup=admin_kb())


@router.message(AdminStates.waiting_unban_id)
async def process_unban(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text and message.text.strip().lower() in ("/cancel", "cancel"):
        await state.clear()
        await message.answer("Отменено.", reply_markup=admin_kb())
        return
    try:
        user_id = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("Нужен числовой ID.")
        return

    await user_service.set_ban(user_id, False)
    await state.clear()
    await message.answer(f"✅ <code>{user_id}</code> разбанен.", reply_markup=admin_kb())


@router.callback_query(F.data == "admin:revoke")
async def admin_revoke_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_revoke_id)
    await callback.message.edit_text(
        "❌ Отправь Telegram ID, у кого снять подписку:\n\n(/cancel — отмена)"
    )
    await callback.answer()


@router.message(AdminStates.waiting_revoke_id)
async def admin_revoke_do(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text and message.text.strip().lower() in ("/cancel", "cancel"):
        await state.clear()
        await message.answer("Отменено.", reply_markup=admin_kb())
        return
    try:
        user_id = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("Нужен числовой ID.")
        return

    await state.clear()
    sub = await user_service.get_active_subscription(user_id)
    if not sub:
        await message.answer(
            f"У <code>{user_id}</code> нет активной подписки.",
            reply_markup=admin_kb(),
        )
        return

    import aiosqlite
    from loader import settings as s

    async with aiosqlite.connect(s.db_path) as db:
        await db.execute(
            "UPDATE subscriptions SET is_active = 0 WHERE id = ?",
            (sub["id"],),
        )
        await db.commit()

    await message.answer(
        f"✅ Подписка пользователя <code>{user_id}</code> снята.",
        reply_markup=admin_kb(),
    )