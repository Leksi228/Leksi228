import logging
from typing import Any, Dict, List, Optional, Tuple

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

from .config import ESCORT_ADMIN_IDS, ESCORT_BOT_TOKEN, ESCORT_LOG_CHAT_ID
from .keyboards import (
    admin_design_keyboard,
    admin_buttons_keyboard,
    admin_main_keyboard,
    admin_model_actions_keyboard,
    admin_models_keyboard,
    admin_sections_keyboard,
    main_menu_keyboard,
    model_detail_keyboard,
    models_list_keyboard,
    payment_keyboard,
    profile_keyboard,
    topup_keyboard,
)
from .storage import EscortData, EscortProfile, ensure_profile, load_data, save_data, update_profile

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# Conversation states
CITY, TOPUP_AMOUNT, ADMIN_MENU, ADMIN_TEXT = range(4)


# ----------------------------
# Storage helpers
# ----------------------------

def _get_storage(context: ContextTypes.DEFAULT_TYPE) -> EscortData:
    return context.application.bot_data.setdefault("storage", load_data())


def _get_profile(context: ContextTypes.DEFAULT_TYPE, user_id: int, username: str) -> Tuple[EscortData, EscortProfile]:
    data = _get_storage(context)
    profile = ensure_profile(data, user_id, username)
    save_data(data)
    return data, profile


# ----------------------------
# Texts
# ----------------------------

def _profile_text(profile: EscortProfile) -> str:
    return (
        "<b>Профиль</b>\n\n"
        f"Имя пользователя: <code>{profile.username or profile.user_id}</code>\n"
        f"ID: <code>{profile.user_id}</code>\n"
        f"Город: <code>{profile.city or 'не задан'}</code>\n\n"
        f"Баланс: <code>{profile.balance_rub}₽</code>\n"
        f"Оформления: <code>{profile.orders_count}</code>"
    )


def _topup_text() -> str:
    return (
        "<b>Пополнение баланса</b>\n\n"
        "Минимальная сумма пополнения: <code>2000₽</code>\n\n"
        "<b>Введите сумму пополнения:</b>"
    )


def _model_text(model: Dict[str, Any]) -> str:
    name = str(model.get("name") or "Модель")
    price = str(model.get("price") or "—")
    desc = str(model.get("desc") or "").strip()
    cities = model.get("cities")
    cities_text = ""
    if isinstance(cities, list) and cities:
        if "*" in cities:
            cities_text = "\nГорода: <code>все</code>"
        else:
            cities_text = "\nГорода: <code>" + ", ".join(map(str, cities)) + "</code>"

    text = f"<b>{name}</b>\nЦена: <code>{price}</code>{cities_text}"
    if desc:
        text += f"\n\n{desc}"
    return text


def _normalize_city(city: str) -> str:
    return city.strip().lower()


def _model_matches_city(model: Dict[str, Any], city: str) -> bool:
    cities = model.get("cities")
    if not cities:
        return True
    if not isinstance(cities, list):
        return True
    norm_city = _normalize_city(city)
    norm = {_normalize_city(str(c)) for c in cities}
    return "*" in norm or norm_city in norm


def _models_for_user(data: EscortData, city: str) -> List[Tuple[int, Dict[str, Any]]]:
    result: List[Tuple[int, Dict[str, Any]]] = []
    for idx, model in enumerate(data.models):
        try:
            if _model_matches_city(model, city):
                result.append((idx, model))
        except Exception:
            # If some old model structure is broken, still keep it visible.
            result.append((idx, model))
    return result


# ----------------------------
# User flow
# ----------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    user = update.effective_user
    if not user:
        return ConversationHandler.END

    data, profile = _get_profile(context, user.id, user.username or user.full_name or "")

    # Worker referral
    worker_id: Optional[int] = None
    if context.args:
        arg = str(context.args[0]).strip()
        if arg.isdigit():
            worker_id = int(arg)
            profile.worker_id = worker_id
            update_profile(data, profile)
            save_data(data)

    # Log new /start
    if ESCORT_LOG_CHAT_ID:
        log_text = (
            "Новый мамонт! "
            f"Привязан к воркеру: {profile.worker_id or 'не привязан'} "
            f"(id: {user.id}, username: @{user.username or 'нет'})"
        )
        try:
            await context.bot.send_message(chat_id=int(ESCORT_LOG_CHAT_ID), text=log_text)
        except Exception:
            logger.exception("Не удалось отправить лог в чат.")

    # City already chosen -> show menu
    if profile.city:
        await update.message.reply_text(
            str(data.settings.get("menu_text", "Главное меню:")),
            reply_markup=main_menu_keyboard(data.settings),
        )
        return ConversationHandler.END

    # Ask city once
    await update.message.reply_text(str(data.settings.get("welcome_text")))
    # If user has to set it, we do.
    context.user_data["force_city_change"] = True
    return CITY


async def city_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Force city change."""
    if not update.message:
        return ConversationHandler.END

    data = _get_storage(context)
    await update.message.reply_text(
        "Введите ваш город (он будет сохранён):",
        reply_markup=None,
    )
    context.user_data["force_city_change"] = True
    return CITY


async def city_from_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END
    await query.answer()

    context.user_data["force_city_change"] = True
    await query.edit_message_text("Введите ваш город (он будет сохранён):")
    return CITY


async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    user = update.effective_user
    if not user:
        return ConversationHandler.END

    city = (update.message.text or "").strip()
    if not city:
        await update.message.reply_text("Введите город текстом.")
        return CITY

    data, profile = _get_profile(context, user.id, user.username or user.full_name or "")

    force = bool(context.user_data.pop("force_city_change", False))
    if profile.city and not force:
        # Do not overwrite city silently.
        await update.message.reply_text(
            "Город уже сохранён. Чтобы изменить — нажми «Сменить город» в меню или /city.",
            reply_markup=main_menu_keyboard(data.settings),
        )
        return ConversationHandler.END

    profile.city = city
    update_profile(data, profile)
    save_data(data)

    await update.message.reply_text(
        str(data.settings.get("menu_text", "Главное меню:")),
        reply_markup=main_menu_keyboard(data.settings),
    )
    return ConversationHandler.END


async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Any random text in private чат: show menu, but don't reset city."""
    if not update.message:
        return
    user = update.effective_user
    if not user:
        return

    data, profile = _get_profile(context, user.id, user.username or user.full_name or "")
    if not profile.city:
        # If city is not set yet, treat message as city.
        context.user_data["force_city_change"] = True
        await handle_city(update, context)
        return

    await update.message.reply_text(
        str(data.settings.get("menu_text", "Главное меню:")),
        reply_markup=main_menu_keyboard(data.settings),
    )


# ----------------------------
# User меню callbacks
# ----------------------------

async def menu_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    user = update.effective_user
    if not user:
        return

    data, profile = _get_profile(context, user.id, user.username or user.full_name or "")

    if query.data == "menu:profile":
        await query.edit_message_text(
            _profile_text(profile),
            reply_markup=profile_keyboard(data.settings),
            parse_mode=ParseMode.HTML,
        )
        return

    if query.data == "menu:support":
        support = str(data.settings.get("support_username") or "@EmeransClubSupport_bot")
        await query.edit_message_text(
            f"Для поддержки напишите: {support}",
            reply_markup=main_menu_keyboard(data.settings),
        )
        return

    if query.data == "menu:info":
        title = str(data.settings.get("title") or (context.bot.username or "Escort"))
        channel = str(data.settings.get("channel_link") or "не задана")
        await query.edit_message_text(
            f"<b>Информация о {title}</b>\n\nСсылка на приватный канал: {channel}",
            reply_markup=main_menu_keyboard(data.settings),
            parse_mode=ParseMode.HTML,
        )
        return

    if query.data == "menu:models":
        if not profile.city:
            context.user_data["force_city_change"] = True
            await query.edit_message_text("Для начала введи город:")
            return

        items = _models_for_user(data, profile.city)
        context.user_data["models_page"] = 0
        if not items:
            await query.edit_message_text(
                "Пока нет моделей для твоего города.\n\nНажми «Сменить город» или попробуй позже.",
                reply_markup=main_menu_keyboard(data.settings),
            )
            return

        await query.edit_message_text(
            f"<b>Модели в городе:</b> <code>{profile.city}</code>",
            reply_markup=models_list_keyboard(data.settings, items, page=0),
            parse_mode=ParseMode.HTML,
        )
        return

    # menu:city is processed by city conversation handler (entry point)


async def models_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    user = update.effective_user
    if not user:
        return

    data, profile = _get_profile(context, user.id, user.username or user.full_name or "")

    if not profile.city:
        context.user_data["force_city_change"] = True
        await query.edit_message_text("Для начала введи город:")
        return

    items = _models_for_user(data, profile.city)

    if query.data == "models:back":
        await query.edit_message_text(
            str(data.settings.get("menu_text", "Главное меню:")),
            reply_markup=main_menu_keyboard(data.settings),
        )
        return

    if query.data.startswith("models:page:"):
        try:
            page = int(query.data.split(":")[-1])
        except Exception:
            page = 0
        page = max(page, 0)
        context.user_data["models_page"] = page
        await query.edit_message_text(
            f"<b>Модели в городе:</b> <code>{profile.city}</code>",
            reply_markup=models_list_keyboard(data.settings, items, page=page),
            parse_mode=ParseMode.HTML,
        )
        return


async def model_open(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    user = update.effective_user
    if not user:
        return

    data, profile = _get_profile(context, user.id, user.username or user.full_name or "")
    if not profile.city:
        context.user_data["force_city_change"] = True
        await query.edit_message_text("Для начала введи город:")
        return

    if query.data == "model:back":
        page = int(context.user_data.get("models_page", 0) or 0)
        items = _models_for_user(data, profile.city)
        await query.edit_message_text(
            f"<b>Модели в городе:</b> <code>{profile.city}</code>",
            reply_markup=models_list_keyboard(data.settings, items, page=page),
            parse_mode=ParseMode.HTML,
        )
        return

    if query.data.startswith("model:"):
        try:
            model_id = int(query.data.split(":")[1])
        except Exception:
            return
        if model_id < 0 or model_id >= len(data.models):
            await query.edit_message_text("Модель не найдена.", reply_markup=main_menu_keyboard(data.settings))
            return

        model = data.models[model_id]
        context.user_data["current_model_id"] = model_id

        await query.edit_message_text(
            _model_text(model),
            reply_markup=model_detail_keyboard(data.settings, link=str(model.get("link") or "")),
            parse_mode=ParseMode.HTML,
        )


async def profile_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    await query.answer()
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    data, profile = _get_profile(context, user.id, user.username or user.full_name or "")

    if query.data == "profile:back":
        await query.edit_message_text(
            str(data.settings.get("menu_text", "Главное меню:")),
            reply_markup=main_menu_keyboard(data.settings),
        )
        return ConversationHandler.END

    if query.data == "profile:favorites":
        await query.edit_message_text(
            "Функция избранного в разработке.",
            reply_markup=profile_keyboard(data.settings),
        )
        return ConversationHandler.END

    if query.data == "profile:topup":
        await query.edit_message_text(
            _topup_text(),
            reply_markup=topup_keyboard(data.settings),
            parse_mode=ParseMode.HTML,
        )
        return TOPUP_AMOUNT

    return ConversationHandler.END


async def topup_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END
    await query.answer()

    user = update.effective_user
    if not user:
        return ConversationHandler.END

    data, _ = _get_profile(context, user.id, user.username or user.full_name or "")
    await query.edit_message_text(
        str(data.settings.get("menu_text", "Главное меню:")),
        reply_markup=main_menu_keyboard(data.settings),
    )
    return ConversationHandler.END


async def handle_topup_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    amount_text = (update.message.text or "").strip().replace("₽", "").replace(" ", "").replace(",", ".")
    try:
        amount_value = float(amount_text)
    except ValueError:
        await update.message.reply_text("Введите корректную сумму.")
        return TOPUP_AMOUNT

    if amount_value < 2000:
        await update.message.reply_text("Минимальная сумма пополнения — 2000₽. Введите другую сумму:")
        return TOPUP_AMOUNT

    context.user_data["topup_amount"] = int(amount_value)
    await update.message.reply_text(
        f"Пополнение: <b>{int(amount_value)}₽</b>\nВыберите метод оплаты:",
        reply_markup=payment_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    return ConversationHandler.END


async def payment_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    method = query.data.split(":", 1)[-1]
    amount = int(context.user_data.get("topup_amount", 0) or 0)

    if method == "card":
        await query.edit_message_text(
            f"Оплата картой (сумма: {amount}₽) — в разработке.\n\nНапиши администратору для реквизитов.",
            reply_markup=None,
        )
        return

    if method == "cash":
        await query.edit_message_text(
            f"Оплата наличными (сумма: {amount}₽) — в разработке.\n\nНапиши администратору для уточнения.",
            reply_markup=None,
        )
        return


# ----------------------------
# Inline search
# ----------------------------

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query
    if not query:
        return

    data = _get_storage(context)
    text_q = (query.query or "").strip().lower()

    results = []
    for idx, model in enumerate(data.models):
        name = str(model.get("name") or "Модель")
        price = str(model.get("price") or "—")
        link = str(model.get("link") or "")
        desc = str(model.get("desc") or "")

        if text_q and text_q not in name.lower() and text_q not in desc.lower():
            continue

        text = f"💞 {name}\nЦена: {price}"
        if link:
            text += f"\nСсылка: {link}"
        if desc:
            text += f"\n\n{desc}"

        results.append(
            InlineQueryResultArticle(
                id=str(idx),
                title=name,
                input_message_content=InputTextMessageContent(text),
            )
        )

    await query.answer(results[:50], cache_time=1)


# ----------------------------
# Admin panel
# ----------------------------

def _is_admin(user_id: int) -> bool:
    return user_id in set(ESCORT_ADMIN_IDS or [])


def _admin_input_keyboard(back_to: str = "admin:back"):
    return (
        [
            [InlineKeyboardButton("⬅️ Назад", callback_data=back_to)],
            [InlineKeyboardButton("❌ Закрыть", callback_data="admin:close")],
        ]
    )


async def admin_open(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    user = update.effective_user
    if not user or not _is_admin(user.id):
        await update.message.reply_text("Доступ ограничен.")
        return ConversationHandler.END

    await update.message.reply_text("Админка:", reply_markup=admin_main_keyboard())
    return ADMIN_MENU


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    user = update.effective_user
    if not user or not _is_admin(user.id):
        await query.answer("Нет доступа", show_alert=True)
        return ConversationHandler.END

    await query.answer()
    data = _get_storage(context)

    payload = query.data or ""

    if payload == "admin:close":
        await query.edit_message_text("Админка закрыта.")
        return ConversationHandler.END

    if payload in ("admin:back", "admin:home"):
        await query.edit_message_text("Админка:", reply_markup=admin_main_keyboard())
        return ADMIN_MENU

    if payload == "admin:models":
        await query.edit_message_text("Модели:", reply_markup=admin_models_keyboard(data.models, page=0))
        return ADMIN_MENU

    if payload.startswith("admin:models_page:"):
        try:
            page = int(payload.split(":")[-1])
        except Exception:
            page = 0
        page = max(page, 0)
        await query.edit_message_text("Модели:", reply_markup=admin_models_keyboard(data.models, page=page))
        return ADMIN_MENU

    if payload == "admin:model_add":
        context.user_data["admin_new_model"] = {}
        context.user_data["admin_input"] = {"action": "add_model", "step": "name"}
        await query.edit_message_text(
            "➕ Добавление модели\n\nОтправьте <b>имя</b> модели:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(_admin_input_keyboard(back_to="admin:models")),
        )
        return ADMIN_TEXT

    if payload.startswith("admin:model:"):
        try:
            model_id = int(payload.split(":")[-1])
        except Exception:
            model_id = -1
        if model_id < 0 or model_id >= len(data.models):
            await query.edit_message_text("Модель не найдена.", reply_markup=admin_models_keyboard(data.models))
            return ADMIN_MENU

        model = data.models[model_id]
        await query.edit_message_text(
            f"<b>Модель #{model_id}</b>\n\n{_model_text(model)}",
            parse_mode=ParseMode.HTML,
            reply_markup=admin_model_actions_keyboard(model_id),
        )
        return ADMIN_MENU

    if payload.startswith("admin:delete:"):
        try:
            model_id = int(payload.split(":")[-1])
        except Exception:
            model_id = -1
        if 0 <= model_id < len(data.models):
            del data.models[model_id]
            save_data(data)
        await query.edit_message_text("Модели:", reply_markup=admin_models_keyboard(data.models, page=0))
        return ADMIN_MENU

    if payload.startswith("admin:edit:"):
        # admin:edit:<id>:<field>
        parts = payload.split(":")
        if len(parts) != 4:
            return ADMIN_MENU
        try:
            model_id = int(parts[2])
        except Exception:
            return ADMIN_MENU
        field = parts[3]
        if model_id < 0 or model_id >= len(data.models):
            return ADMIN_MENU

        hints = {
            "name": "Введите <b>имя</b> модели:",
            "price": "Введите <b>цену</b> (например: 5000₽):",
            "link": "Введите <b>ссылку</b> (https://t.me/...):",
            "cities": "Введите города через запятую (например: Amsterdam, Rotterdam) или <code>all</code>:",
            "desc": "Введите <b>описание</b> (можно несколькими строками):",
        }

        context.user_data["admin_input"] = {"action": "edit_model", "model_id": model_id, "field": field}
        await query.edit_message_text(
            hints.get(field, "Введите значение:"),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(_admin_input_keyboard(back_to=f"admin:model:{model_id}")),
        )
        return ADMIN_TEXT

    if payload == "admin:design":
        await query.edit_message_text("Дизайн/настройки:", reply_markup=admin_design_keyboard(data.settings))
        return ADMIN_MENU

    if payload == "admin:design_buttons":
        await query.edit_message_text(
            "Подписи кнопок:",
            reply_markup=admin_buttons_keyboard(data.settings),
        )
        return ADMIN_MENU

    if payload == "admin:design_sections":
        await query.edit_message_text(
            "Выбор разделов главного меню:",
            reply_markup=admin_sections_keyboard(data.settings),
        )
        return ADMIN_MENU

    if payload.startswith("admin:toggle_section:"):
        key = payload.split(":", 2)[-1]
        sections = data.settings.get("menu_sections", [])
        if not isinstance(sections, list):
            sections = []
        sections = [str(s) for s in sections]
        if key in sections:
            sections = [s for s in sections if s != key]
        else:
            sections.append(key)
        data.settings["menu_sections"] = sections
        save_data(data)
        await query.edit_message_text(
            "Выбор разделов главного меню:",
            reply_markup=admin_sections_keyboard(data.settings),
        )
        return ADMIN_MENU

    if payload.startswith("admin:design_set:"):
        setting_key = payload.split(":")[-1]
        context.user_data["admin_input"] = {"action": "set_setting", "key": setting_key}
        await query.edit_message_text(
            f"Отправьте новое значение для <code>{setting_key}</code>:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(_admin_input_keyboard(back_to="admin:design")),
        )
        return ADMIN_TEXT

    if payload.startswith("admin:btn_set:"):
        setting_key = payload.split(":")[-1]
        context.user_data["admin_input"] = {"action": "set_setting", "key": setting_key}
        await query.edit_message_text(
            f"Отправьте новую подпись для <code>{setting_key}</code>:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(_admin_input_keyboard(back_to="admin:design_buttons")),
        )
        return ADMIN_TEXT

    return ADMIN_MENU


async def admin_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    user = update.effective_user
    if not user or not _is_admin(user.id):
        await update.message.reply_text("Доступ ограничен.")
        return ConversationHandler.END

    data = _get_storage(context)
    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text("Пустое значение. Отправьте текст.")
        return ADMIN_TEXT

    meta = context.user_data.get("admin_input") or {}
    action = meta.get("action")

    if action == "set_setting":
        key = str(meta.get("key"))
        data.settings[key] = text
        save_data(data)
        await update.message.reply_text("✅ Обновлено.")
        return ConversationHandler.END

    if action == "edit_model":
        try:
            model_id = int(meta.get("model_id"))
        except Exception:
            return ConversationHandler.END
        field = str(meta.get("field"))
        if model_id < 0 or model_id >= len(data.models):
            await update.message.reply_text("Модель не найдена.")
            return ConversationHandler.END

        model = data.models[model_id]

        if field == "cities":
            if text.lower() in ("all", "*", "все"):
                model["cities"] = ["*"]
            else:
                cities = [c.strip() for c in text.split(",") if c.strip()]
                model["cities"] = cities
        else:
            model[field] = text

        save_data(data)
        await update.message.reply_text("✅ Модель обновлена.")
        return ConversationHandler.END

    if action == "add_model":
        new_model = context.user_data.get("admin_new_model")
        if not isinstance(new_model, dict):
            new_model = {}
            context.user_data["admin_new_model"] = new_model

        step = meta.get("step")
        if step == "name":
            new_model["name"] = text
            context.user_data["admin_input"] = {"action": "add_model", "step": "price"}
            await update.message.reply_text("Введите цену модели (например: 5000₽):")
            return ADMIN_TEXT

        if step == "price":
            new_model["price"] = text
            context.user_data["admin_input"] = {"action": "add_model", "step": "link"}
            await update.message.reply_text("Введите ссылку (https://t.me/...):")
            return ADMIN_TEXT

        if step == "link":
            new_model["link"] = text
            context.user_data["admin_input"] = {"action": "add_model", "step": "cities"}
            await update.message.reply_text("Введите города через запятую или all:")
            return ADMIN_TEXT

        if step == "cities":
            if text.lower() in ("all", "*", "все"):
                new_model["cities"] = ["*"]
            else:
                new_model["cities"] = [c.strip() for c in text.split(",") if c.strip()]
            context.user_data["admin_input"] = {"action": "add_model", "step": "desc"}
            await update.message.reply_text("Введите описание модели (или '-' если не нужно):")
            return ADMIN_TEXT

        if step == "desc":
            if text != "-":
                new_model["desc"] = text
            data.models.append(new_model)
            save_data(data)
            context.user_data.pop("admin_new_model", None)
            context.user_data.pop("admin_input", None)
            await update.message.reply_text("✅ Модель добавлена.")
            return ConversationHandler.END

    await update.message.reply_text("Не понял действие. Открой админку заново: /admin")
    return ConversationHandler.END


# ----------------------------
# Main
# ----------------------------


def main() -> None:
    if not ESCORT_BOT_TOKEN:
        raise RuntimeError("ESCORT_BOT_TOKEN is required")

    app = ApplicationBuilder().token(ESCORT_BOT_TOKEN).build()

    # Conversations (must be registered BEFORE broad callback handlers)
    city_conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("city", city_cmd),
            CallbackQueryHandler(city_from_menu, pattern=r"^menu:city$"),
        ],
        states={
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city)],
        },
        fallbacks=[CommandHandler("start", start)],
        name="city_conv",
        persistent=False,
    )
    app.add_handler(city_conv)

    # User callbacks
    # (menu:city is handled by city_conv entry point)
    app.add_handler(CallbackQueryHandler(menu_action, pattern=r"^menu:(models|profile|support|info)$"))
    app.add_handler(CallbackQueryHandler(models_action, pattern=r"^models:"))
    app.add_handler(CallbackQueryHandler(model_open, pattern=r"^model:"))
    app.add_handler(CallbackQueryHandler(payment_action, pattern=r"^pay:"))

    topup_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(profile_action, pattern=r"^profile:" )],
        states={
            TOPUP_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_topup_amount)],
        },
        fallbacks=[CallbackQueryHandler(topup_back, pattern=r"^topup:back$")],
        name="topup_conv",
        persistent=False,
    )
    app.add_handler(topup_conv)

    # Admin conversation
    admin_conv = ConversationHandler(
        entry_points=[CommandHandler("admin", admin_open)],
        states={
            ADMIN_MENU: [CallbackQueryHandler(admin_callback, pattern=r"^admin:")],
            ADMIN_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_text_input)],
        },
        fallbacks=[CommandHandler("admin", admin_open)],
        name="admin_conv",
        persistent=False,
    )
    app.add_handler(admin_conv)

    # Inline query
    app.add_handler(InlineQueryHandler(inline_query))

    # Fallback: any text in private chat => show menu (without resetting city)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, unknown_text))

    app.run_polling()


if __name__ == "__main__":
    main()
