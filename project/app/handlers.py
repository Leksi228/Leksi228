import io
import logging
from datetime import datetime, timezone, timedelta

from PIL import Image, ImageDraw, ImageFont
from telegram import InputFile, InputMediaPhoto, Update
from telegram.ext import ContextTypes, ConversationHandler

from app.config import ADMIN_CHAT_ID, ADMIN_USER_IDS
from app.keyboards import (
    about_links_keyboard,
    admin_decision_keyboard,
    admin_menu_keyboard,
    apply_keyboard,
    design_sections_keyboard,
    directions_keyboard,
    links_sections_keyboard,
    main_menu_keyboard,
    origin_keyboard,
    profile_keyboard,
    profits_curator_keyboard,
    profits_multiplier_keyboard,
    profits_rate_keyboard,
    profits_service_keyboard,
    time_keyboard,
    withdraw_request_keyboard,
    wallet_keyboard,
)
from app.storage import BotData, ensure_profile, load_data, save_data, update_profile

logger = logging.getLogger(__name__)

(
    ORIGIN,
    TIME,
    ABOUT,
    NICKNAME,
    DESCRIPTION,
    DESIGN_BANNER,
    MENTOR_ADD,
    PROFIT_USER_ID,
    PROFIT_SERVICE,
    PROFIT_AMOUNT,
    PROFIT_RATE,
    PROFIT_MENTOR,
    PROFIT_MULTIPLIER,
    PROFIT_CHANNEL,
    BALANCE_USER_ID,
    BALANCE_AMOUNT,
    LINKS_SECTION,
    LINKS_URL,
    WITHDRAW_AMOUNT,
) = range(19)


def _get_storage(context: ContextTypes.DEFAULT_TYPE) -> BotData:
    data = context.application.bot_data.setdefault("storage", load_data())
    if not hasattr(data, "links"):
        data.links = {}
        save_data(data)
    if not hasattr(data, "profit_count"):
        data.profit_count = 0
        data.profit_total_rub = 0
        save_data(data)
    return data


async def _update_profile_message(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    username: str,
    profile,
) -> bool:
    data = _get_storage(context)
    banner_id = data.banners.get("profile")
    text = _profile_text(user_id, username, profile)
    chat_id = context.user_data.get("profile_chat_id")
    message_id = context.user_data.get("profile_message_id")
    if not chat_id or not message_id:
        return False

    try:
        if banner_id:
            media = await _build_profile_media(
                context, user_id, username, profile, caption=text, parse_mode="HTML"
            )
            if not media:
                return False
            if isinstance(media.media, InputFile):
                sent = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=media.media,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=profile_keyboard(profile.show_nickname_in_profits),
                )
                try:
                    await context.bot.delete_message(
                        chat_id=chat_id,
                        message_id=message_id,
                    )
                except Exception:
                    logger.exception("Не удалось удалить старое сообщение профиля.")
                context.user_data["profile_chat_id"] = sent.chat_id
                context.user_data["profile_message_id"] = sent.message_id
            else:
                await context.bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=message_id,
                    media=media,
                    reply_markup=profile_keyboard(profile.show_nickname_in_profits),
                )
        else:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=profile_keyboard(profile.show_nickname_in_profits),
                parse_mode="HTML",
            )
    except Exception:
        logger.exception("Не удалось обновить сообщение профиля.")
        return False
    return True


def _format_user_link(user_id: int, label: str) -> str:
    return f"<a href=\"tg://user?id={user_id}\">{label}</a>"


def _profit_window_counts(profile, now: datetime) -> tuple[int, int, int]:
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    daily = weekly = monthly = 0
    for item in profile.profit_history or []:
        ts = item.get("ts")
        if not ts:
            continue
        try:
            created = datetime.fromisoformat(ts)
        except ValueError:
            continue
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if created >= day_ago:
            daily += 1
        if created >= week_ago:
            weekly += 1
        if created >= month_ago:
            monthly += 1
    return daily, weekly, monthly


def _profile_text(user_id: int, username: str, profile) -> str:
    nickname = profile.nickname or username
    nickname = nickname if nickname else f"ID {user_id}"
    nickname_link = _format_user_link(user_id, nickname)
    profits_amount = f"{profile.profit_total_rub} RUB ({profile.profit_count})"
    days_with_us = _days_with_us(profile.first_seen)
    description = profile.description or "не указано"
    now = datetime.now(timezone.utc)
    daily, weekly, monthly = _profit_window_counts(profile, now)
    return (
        f"👤 Никнейм: {nickname_link}\n"
        f"┖ Статус: {profile.status}\n\n"
        f"📊 {profile.profit_count} профитов на сумму:\n"
        f"┖ {profits_amount}. (в будущем разработаем систему профитов! от этого "
        f"будет считаться общая сумма профитов!)\n\n"
        f"📆 Профиты за день: {daily}\n"
        f"📅 Профиты за неделю: {weekly}\n"
        f"🗓️ Профиты за месяц: {monthly}\n\n"
        f"💬 Описание: {description}\n"
        f"👥 С нами: {days_with_us} дней"
    )


def _days_with_us(first_seen: str) -> int:
    try:
        created_at = datetime.fromisoformat(first_seen)
    except ValueError:
        return 0
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return max((now - created_at).days, 0)


async def _edit_message(
    query, text: str, reply_markup=None, parse_mode: str | None = None
) -> None:
    if query.message and query.message.photo:
        await query.edit_message_caption(
            caption=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    else:
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )


async def _show_banner_or_text(
    query,
    banner_id: str | None,
    text: str,
    reply_markup=None,
    parse_mode: str | None = None,
) -> None:
    if not banner_id:
        await _edit_message(query, text, reply_markup=reply_markup, parse_mode=parse_mode)
        return

    if query.message and query.message.photo:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=banner_id, caption=text, parse_mode=parse_mode
            ),
            reply_markup=reply_markup,
        )
        return

    if query.message:
        sent = await query.message.reply_photo(
            photo=banner_id,
            caption=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
        try:
            await query.message.delete()
        except Exception:
            logger.exception("Не удалось удалить старое сообщение.")
        else:
            context.user_data["last_banner_chat_id"] = sent.chat_id
            context.user_data["last_banner_message_id"] = sent.message_id
        return

    await _edit_message(query, text, reply_markup=reply_markup, parse_mode=parse_mode)


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (
        "fonts/RussoOne-Regular.ttf",
        "C:\\Fexoya\\RussoOne-Regular.ttf",
        "C:\\Fexoya\\RussoOne-Regular.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


async def _build_profile_media(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    username: str,
    profile,
    caption: str | None = None,
    parse_mode: str | None = None,
) -> InputMediaPhoto | None:
    data = _get_storage(context)
    banner_id = data.banners.get("profile")
    if not banner_id:
        return None
    try:
        banner_file = await context.bot.get_file(banner_id)
        banner_bytes = await banner_file.download_as_bytearray()
    except Exception:
        logger.exception("Не удалось скачать баннер профиля.")
        return None
    try:
        image = Image.open(io.BytesIO(banner_bytes)).convert("RGBA")
    except Exception:
        logger.exception("Не удалось открыть баннер профиля.")
        return None

    width, height = image.size
    scale_x = width / 1280
    scale_y = height / 720
    avatar_size = int(169 * scale_x)
    avatar_x = int(142 * scale_x)
    avatar_y = int(100 * scale_y)
    worker_x = int(510 * scale_x)
    worker_y = int(137 * scale_y)
    profit_x = int(469 * scale_x)
    profit_y = int(367 * scale_y)
    days_x = int(390 * scale_x)
    days_y = int(497 * scale_y)

    draw = ImageDraw.Draw(image)
    font_main = _load_font(int(36 * scale_y))
    font_secondary = _load_font(int(26 * scale_y))
    nickname = profile.nickname or username or f"ID {user_id}"
    days_with_us = _days_with_us(profile.first_seen)
    profits_amount = f"{profile.profit_total_rub} RUB ({profile.profit_count})"

    draw.text((worker_x, worker_y), nickname, font=font_main, fill="white")
    draw.text((profit_x, profit_y), profits_amount, font=font_secondary, fill="white")
    draw.text((days_x, days_y), str(days_with_us), font=font_secondary, fill="white")

    try:
        photos = await context.bot.get_user_profile_photos(user_id, limit=1)
    except Exception:
        photos = None
    if photos and photos.total_count > 0:
        photo = photos.photos[0][-1]
        try:
            avatar_file = await context.bot.get_file(photo.file_id)
            avatar_bytes = await avatar_file.download_as_bytearray()
            avatar_image = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
            avatar_image = avatar_image.resize((avatar_size, avatar_size))
            image.paste(avatar_image, (avatar_x, avatar_y))
        except Exception:
            logger.exception("Не удалось загрузить аватар.")

    output = io.BytesIO()
    image.convert("RGB").save(output, format="JPEG", quality=92)
    output.seek(0)
    input_file = InputFile(output, filename="profile.jpg")
    return InputMediaPhoto(media=input_file, caption=caption, parse_mode=parse_mode)


async def _show_profile_banner(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    username: str,
    profile,
) -> None:
    text = _profile_text(user_id, username, profile)
    media = await _build_profile_media(
        context, user_id, username, profile, caption=text, parse_mode="HTML"
    )
    if not media:
        await _edit_message(
            query,
            text,
            reply_markup=profile_keyboard(profile.show_nickname_in_profits),
            parse_mode="HTML",
        )
        return
    if query.message and query.message.photo:
        if isinstance(media.media, InputFile):
            sent = await query.message.reply_photo(
                photo=media.media,
                caption=text,
                parse_mode="HTML",
                reply_markup=profile_keyboard(profile.show_nickname_in_profits),
            )
            try:
                await query.message.delete()
            except Exception:
                logger.exception("Не удалось удалить старое сообщение профиля.")
            context.user_data["profile_chat_id"] = sent.chat_id
            context.user_data["profile_message_id"] = sent.message_id
        else:
            await query.edit_message_media(
                media=media,
                reply_markup=profile_keyboard(profile.show_nickname_in_profits),
            )
        return
    if query.message:
        sent = await query.message.reply_photo(
            photo=media.media,
            caption=text,
            parse_mode="HTML",
            reply_markup=profile_keyboard(profile.show_nickname_in_profits),
        )
        try:
            await query.message.delete()
        except Exception:
            logger.exception("Не удалось удалить старое сообщение профиля.")
        context.user_data["profile_chat_id"] = sent.chat_id
        context.user_data["profile_message_id"] = sent.message_id
        return
    await _edit_message(
        query,
        _profile_text(user_id, username, profile),
        reply_markup=profile_keyboard(profile.show_nickname_in_profits),
        parse_mode="HTML",
    )


async def _send_profile_banner_message(
    message,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    username: str,
    profile,
) -> None:
    text = _profile_text(user_id, username, profile)
    media = await _build_profile_media(
        context, user_id, username, profile, caption=text, parse_mode="HTML"
    )
    if media:
        await message.reply_photo(
            photo=media.media,
            caption=text,
            parse_mode="HTML",
            reply_markup=profile_keyboard(profile.show_nickname_in_profits),
        )
    else:
        await message.reply_text(
            text,
            reply_markup=profile_keyboard(profile.show_nickname_in_profits),
            parse_mode="HTML",
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = _get_storage(context)
    user = update.effective_user
    if not user:
        return

    ensure_profile(data, user.id)
    save_data(data)

    if user.id in data.approved_users:
        is_admin = user.id in ADMIN_USER_IDS
        banner_id = data.banners.get("main")
        if banner_id:
            await update.message.reply_photo(
                photo=banner_id,
                caption="Добро пожаловать! Выберите раздел:",
                reply_markup=main_menu_keyboard(is_admin),
            )
        else:
            await update.message.reply_text(
                "Добро пожаловать! Выберите раздел:",
                reply_markup=main_menu_keyboard(is_admin),
            )
        return

    greeting = "Приветствую вас в команде <b>Nenosens Team</b>"
    await update.message.reply_html(
        greeting,
        reply_markup=apply_keyboard(),
    )


async def apply_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    await query.answer()
    await _edit_message(query, "1. Откуда вы узнали о нас?", reply_markup=origin_keyboard())
    return ORIGIN


async def handle_origin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    await query.answer()
    origin = query.data.split(":", maxsplit=1)[-1]
    context.user_data["origin"] = origin
    await _edit_message(
        query,
        "2. Сколько времени готовы выделять на работу?\n\n«Минималка от 4ч работы»",
        reply_markup=time_keyboard(),
    )
    return TIME


async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    await query.answer()
    time_value = query.data.split(":", maxsplit=1)[-1]
    context.user_data["time"] = time_value
    await _edit_message(query, "3. Расскажите о себе и почему решили подать заявку именно нам?")
    return ABOUT


async def handle_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    about_text = update.message.text
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    context.user_data["about"] = about_text
    await update.message.reply_text(
        "Спасибо! Заявка отправлена на обработку админам."
    )

    data = _get_storage(context)
    data.applications[str(user.id)] = {
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "origin": context.user_data.get("origin"),
        "time": context.user_data.get("time"),
        "about": about_text,
        "status": "pending",
    }
    save_data(data)

    if ADMIN_CHAT_ID:
        text = (
            "Новая заявка:\n"
            f"Пользователь: {user.full_name} (@{user.username or 'без username'})\n"
            f"ID: {user.id}\n"
            f"Откуда узнали: {context.user_data.get('origin')}\n"
            f"Время: {context.user_data.get('time')}\n"
            f"О себе: {about_text}"
        )
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=text,
            reply_markup=admin_decision_keyboard(user.id),
        )
    else:
        logger.warning("ADMIN_CHAT_ID is not set; cannot notify admins.")

    return ConversationHandler.END


async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    await query.answer()
    if ADMIN_CHAT_ID and query.message and query.message.chat_id != ADMIN_CHAT_ID:
        await query.answer("Эта кнопка доступна только администраторам.", show_alert=True)
        return

    parts = query.data.split(":")
    if len(parts) != 3:
        return

    _, action, user_id_str = parts
    user_id = int(user_id_str)

    data = _get_storage(context)
    application = data.applications.get(user_id_str)
    if not application:
        await query.edit_message_text("Заявка не найдена.")
        return

    if action == "accept":
        if user_id not in data.approved_users:
            data.approved_users.append(user_id)
        application["status"] = "accepted"
        save_data(data)
        await _edit_message(query, f"Заявка пользователя {user_id} принята.")
        await context.bot.send_message(
            chat_id=user_id,
            text="Ваша заявка одобрена! Напишите /start для доступа к меню.",
        )
    elif action == "reject":
        application["status"] = "rejected"
        save_data(data)
        await _edit_message(query, f"Заявка пользователя {user_id} отклонена.")
        await context.bot.send_message(
            chat_id=user_id,
            text="К сожалению, ваша заявка отклонена.",
        )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = _get_storage(context)
    user = update.effective_user
    if not user:
        return

    if query.data == "menu:profile":
        profile = ensure_profile(data, user.id)
        save_data(data)
        await _show_profile_banner(
            query,
            context,
            user.id,
            user.full_name or user.username or "",
            profile,
        )
        if query.message:
            context.user_data["profile_chat_id"] = query.message.chat_id
            context.user_data["profile_message_id"] = query.message.message_id
        return

    if query.data == "menu:tracks":
        banner_id = data.banners.get("directions")
        await _show_banner_or_text(
            query,
            banner_id,
            "Выберите направление:",
            reply_markup=directions_keyboard(),
        )
        return

    if query.data == "menu:mentors":
        banner_id = data.banners.get("mentors")
        await _show_banner_or_text(query, banner_id, "Раздел пока в разработке.")
        return

    if query.data == "menu:about":
        banner_id = data.banners.get("about")
        await _show_banner_or_text(
            query,
            banner_id,
            _about_text(data),
            reply_markup=about_links_keyboard(data.links),
            parse_mode="HTML",
        )
        return

    if query.data == "menu:admin":
        if user.id not in ADMIN_USER_IDS:
            await _edit_message(query, "Доступ ограничен.")
            return
        await _edit_message(
            query,
            "Админ-меню:",
            reply_markup=admin_menu_keyboard(),
        )
        return

    await _edit_message(query, "Раздел пока в разработке.")


async def profile_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    await query.answer()
    data = _get_storage(context)
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    profile = ensure_profile(data, user.id)

    if query.data == "profile:back":
        banner_id = data.banners.get("main")
        await _show_banner_or_text(
            query,
            banner_id,
            "Добро пожаловать! Выберите раздел:",
            reply_markup=main_menu_keyboard(user.id in ADMIN_USER_IDS),
        )
        return ConversationHandler.END

    if query.data == "profile:wallet":
        await _edit_message(
            query,
            _wallet_text(profile.balance_rub),
            reply_markup=wallet_keyboard(),
        )
        return ConversationHandler.END

    if query.data == "profile:profits_toggle":
        profile.show_nickname_in_profits = not profile.show_nickname_in_profits
        update_profile(data, profile)
        save_data(data)
        await _show_profile_banner(
            query,
            context,
            user.id,
            user.full_name or user.username or "",
            profile,
        )
        if query.message:
            context.user_data["profile_chat_id"] = query.message.chat_id
            context.user_data["profile_message_id"] = query.message.message_id
        return ConversationHandler.END

    if query.data == "profile:nickname":
        await _edit_message(query, "Введите желаемый никнейм (от 1 до 15 символов):")
        return NICKNAME

    if query.data == "profile:description":
        await _edit_message(query, "Введите желаемое описание вашего профиля (от 1 до 50 символов):")
        return DESCRIPTION

    return ConversationHandler.END


async def handle_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    nickname = update.message.text.strip()
    if not 1 <= len(nickname) <= 15:
        await update.message.reply_text(
            "Никнейм должен быть от 1 до 15 символов. Попробуйте снова:"
        )
        return NICKNAME

    data = _get_storage(context)
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    profile = ensure_profile(data, user.id)
    profile.nickname = nickname
    update_profile(data, profile)
    save_data(data)
    updated = await _update_profile_message(
        context,
        user.id,
        user.full_name or user.username or "",
        profile,
    )
    if not updated:
        await _send_profile_banner_message(
            update.message,
            context,
            user.id,
            user.full_name or user.username or "",
            profile,
        )
    return ConversationHandler.END


async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    description = update.message.text.strip()
    if not 1 <= len(description) <= 50:
        await update.message.reply_text(
            "Описание должно быть от 1 до 50 символов. Попробуйте снова:"
        )
        return DESCRIPTION

    data = _get_storage(context)
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    profile = ensure_profile(data, user.id)
    profile.description = description
    update_profile(data, profile)
    save_data(data)
    updated = await _update_profile_message(
        context,
        user.id,
        user.full_name or user.username or "",
        profile,
    )
    if not updated:
        await _send_profile_banner_message(
            update.message,
            context,
            user.id,
            user.full_name or user.username or "",
            profile,
        )
    return ConversationHandler.END


async def wallet_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    await query.answer()
    if query.data == "wallet:withdraw":
        await _edit_message(query, "Введите сумму вывода:")
        return WITHDRAW_AMOUNT

    if query.data == "wallet:history":
        await _edit_message(
            query,
            "История транзакций пока в разработке.",
            reply_markup=wallet_keyboard(),
        )
        return ConversationHandler.END

    if query.data == "wallet:back":
        data = _get_storage(context)
        user = update.effective_user
        if not user:
            return ConversationHandler.END
        profile = ensure_profile(data, user.id)
        save_data(data)
        await _show_profile_banner(
            query,
            context,
            user.id,
            user.full_name or user.username or "",
            profile,
        )
        return ConversationHandler.END

    return ConversationHandler.END


async def handle_withdraw_amount(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not update.message:
        return ConversationHandler.END

    user = update.effective_user
    if not user:
        return ConversationHandler.END

    amount_text = update.message.text.strip().replace(",", ".")
    try:
        amount_value = float(amount_text)
    except ValueError:
        await update.message.reply_text("Введите корректную сумму.")
        return WITHDRAW_AMOUNT

    if amount_value <= 0:
        await update.message.reply_text("Сумма должна быть больше 0.")
        return WITHDRAW_AMOUNT

    data = _get_storage(context)
    if not ADMIN_CHAT_ID:
        await update.message.reply_text("ADMIN_CHAT_ID не задан.")
        return ConversationHandler.END

    profile = ensure_profile(data, user.id)
    if amount_value > profile.balance_rub:
        await update.message.reply_text("Недостаточно средств на балансе.")
        return WITHDRAW_AMOUNT

    nickname = profile.nickname or user.full_name or user.username or f"ID {user.id}"
    request_text = (
        f"Воркер запросил вывод: {_format_amount(amount_value)} RUB\n"
        f"Воркер: {_format_user_link(user.id, nickname)}\n"
        f"Процент: {profile.payout_rate}%"
    )
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=request_text,
        reply_markup=withdraw_request_keyboard(user.id, amount_value),
        parse_mode="HTML",
    )
    await update.message.reply_text("Запрос на вывод отправлен.")
    return ConversationHandler.END


async def withdraw_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    await query.answer()
    user = update.effective_user
    if not user or user.id not in ADMIN_USER_IDS:
        await _edit_message(query, "Доступ ограничен.")
        return

    parts = query.data.split(":")
    if len(parts) < 4:
        await _edit_message(query, "Некорректная заявка.")
        return

    target_id = int(parts[2])
    amount = parts[3]
    await context.bot.send_message(
        chat_id=target_id,
        text="<b><code>Ожидайте вывод своих средств в течении 24ч!</code></b>",
        parse_mode="HTML",
    )
    await _edit_message(
        query,
        f"Заявка на вывод {amount} RUB взята в обработку.",
    )


def _wallet_text(balance_rub: int) -> str:
    return (
        "Кошелёк 👛\n\n"
        f"💰 Баланс: {balance_rub} RUB\n\n"
        "Доступные способы вывода:\n"
        "CryptoBot - Чек 🧾\n\n"
        "⚠️ Вывод от 500 RUB"
    )


def _about_text(data: BotData) -> str:
    return (
        "🌐 <b>О проекте</b>\n"
        "┖ Дата открытия: 17.01.2026\n\n"
        f"Профитов на сумму: <code>{data.profit_total_rub} RUB</code>\n"
        f"Количество профитов: {data.profit_count}\n\n"
        "Процент выплат:\n"
        "┠ Крипто-деп: <code>80%</code>\n"
        "┠ Пополнение: <code>70%</code>\n"
        "┖ ТП: <code>65%</code>"
    )


async def directions_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    await query.answer()
    if query.data == "direction:back":
        user = update.effective_user
        if not user:
            return
        banner_id = _get_storage(context).banners.get("main")
        await _show_banner_or_text(
            query,
            banner_id,
            "Добро пожаловать! Выберите раздел:",
            reply_markup=main_menu_keyboard(user.id in ADMIN_USER_IDS),
        )
        return
    if query.data == "direction:escort":
        user = update.effective_user
        if not user:
            return
        referral_link = f"t.me/EmeransClub_bot?start={user.id}"
        text = (
            "🦋 Сервис: <b>Escort</b>\n"
            "Название бота для работы: <b>@EmeransClub_bot</b>\n\n"
            "Тех поддержка: <b>@EmeransClubSupport_bot</b>\n\n"
            "Ваша реферальная ссылка:\n\n"
            f"{referral_link}\n"
            "Эта реферальная ссылка привязывает обычного пользователя к воркеру и "
            "она отправляет воркеру логи,а какие логи я напишу позже!"
        )
        await _edit_message(query, text, parse_mode="HTML")
        return

    await _edit_message(query, "Раздел пока в разработке.")


async def admin_menu_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    await query.answer()
    user = update.effective_user
    if not user or user.id not in ADMIN_USER_IDS:
        await _edit_message(query, "Доступ ограничен.")
        return ConversationHandler.END

    if query.data == "admin:back":
        banner_id = _get_storage(context).banners.get("main")
        await _show_banner_or_text(
            query,
            banner_id,
            "Добро пожаловать! Выберите раздел:",
            reply_markup=main_menu_keyboard(True),
        )
        return ConversationHandler.END

    if query.data == "admin:design":
        await _edit_message(
            query,
            "Выберите раздел для баннера:",
            reply_markup=design_sections_keyboard(),
        )
        return ConversationHandler.END

    if query.data == "admin:mentor_add":
        await _edit_message(query, "Введите ID наставника:")
        return MENTOR_ADD

    if query.data == "admin:profit_channel":
        await _edit_message(
            query,
            "Введите ID канала профитов (например, -1001234567890):"
        )
        return PROFIT_CHANNEL

    if query.data == "admin:links":
        await _edit_message(
            query,
            "Выберите раздел для ссылки:",
            reply_markup=links_sections_keyboard(),
        )
        return ConversationHandler.END

    if query.data == "admin:balance_grant":
        await _edit_message(query, "Введите ID пользователя для начисления:")
        return BALANCE_USER_ID

    return ConversationHandler.END


async def profit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    await query.answer()
    user = update.effective_user
    if not user or user.id not in ADMIN_USER_IDS:
        await _edit_message(query, "Доступ ограничен.")
        return ConversationHandler.END

    await _edit_message(query, "Введите ID воркера:")
    return PROFIT_USER_ID


async def about_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    await query.answer()
    if query.data == "about:back":
        data = _get_storage(context)
        user = update.effective_user
        if not user:
            return
        banner_id = data.banners.get("main")
        await _show_banner_or_text(
            query,
            banner_id,
            "Добро пожаловать! Выберите раздел:",
            reply_markup=main_menu_keyboard(user.id in ADMIN_USER_IDS),
        )


async def design_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    await query.answer()
    user = update.effective_user
    if not user or user.id not in ADMIN_USER_IDS:
        await query.edit_message_text("Доступ ограничен.")
        return ConversationHandler.END

    if query.data == "design:back":
        await _edit_message(
            query,
            "Админ-меню:",
            reply_markup=admin_menu_keyboard(),
        )
        return ConversationHandler.END

    _, section = query.data.split(":", maxsplit=1)
    context.user_data["design_section"] = section
    if query.message:
        context.user_data["design_message_id"] = query.message.message_id
        context.user_data["design_chat_id"] = query.message.chat_id
    await _edit_message(query, "Отправьте фото-баннер для выбранного раздела:")
    return DESIGN_BANNER


async def links_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    await query.answer()
    user = update.effective_user
    if not user or user.id not in ADMIN_USER_IDS:
        await _edit_message(query, "Доступ ограничен.")
        return ConversationHandler.END

    if query.data == "links:back":
        await _edit_message(
            query,
            "Админ-меню:",
            reply_markup=admin_menu_keyboard(),
        )
        return ConversationHandler.END

    _, section = query.data.split(":", maxsplit=1)
    context.user_data["links_section"] = section
    await _edit_message(query, "Отправьте ссылку для выбранного раздела:")
    return LINKS_URL


async def handle_links_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    user = update.effective_user
    if not user or user.id not in ADMIN_USER_IDS:
        await update.message.reply_text("Доступ ограничен.")
        return ConversationHandler.END

    url = update.message.text.strip()
    section = context.user_data.get("links_section")
    if not section:
        await update.message.reply_text("Секция не выбрана.")
        return ConversationHandler.END

    data = _get_storage(context)
    data.links[section] = url
    save_data(data)
    section_label = {
        "info": "INFO",
        "manuals": "Мануалы",
        "profits": "Профиты",
        "chat": "Чат",
    }.get(section, section)
    await update.message.reply_text(
        f"Ссылка сохранена для раздела: {section_label}.",
        reply_markup=admin_menu_keyboard(),
    )
    return ConversationHandler.END


async def handle_design_banner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    photo_file_id = None
    if update.message.photo:
        photo_file_id = update.message.photo[-1].file_id
    elif update.message.document and update.message.document.mime_type:
        if update.message.document.mime_type.startswith("image/"):
            photo_file_id = update.message.document.file_id

    if not photo_file_id:
        await update.message.reply_text("Нужно отправить фото-баннер.")
        return DESIGN_BANNER

    user = update.effective_user
    if not user or user.id not in ADMIN_USER_IDS:
        await update.message.reply_text("Доступ ограничен.")
        return ConversationHandler.END

    section = context.user_data.get("design_section")
    if not section:
        await update.message.reply_text("Секция не выбрана.")
        return ConversationHandler.END

    data = _get_storage(context)
    data.banners[section] = photo_file_id
    save_data(data)
    section_label = {
        "main": "Главное меню",
        "directions": "Направления",
        "mentors": "Кураторы",
        "about": "О проекте",
        "profile": "Мой профиль",
    }.get(section, section)
    caption = f"Фотка успешно добавлена на раздел: {section_label}"
    chat_id = context.user_data.get("design_chat_id")
    message_id = context.user_data.get("design_message_id")
    if chat_id and message_id:
        await context.bot.edit_message_media(
            chat_id=chat_id,
            message_id=message_id,
            media=InputMediaPhoto(media=photo_file_id, caption=caption),
            reply_markup=admin_menu_keyboard(),
        )
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
            )
        except Exception:
            logger.exception("Не удалось удалить сообщение с фото.")
    else:
        await update.message.reply_photo(
            photo=photo_file_id,
            caption=caption,
            reply_markup=admin_menu_keyboard(),
        )
    return ConversationHandler.END


async def handle_mentor_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    user = update.effective_user
    if not user or user.id not in ADMIN_USER_IDS:
        await update.message.reply_text("Доступ ограничен.")
        return ConversationHandler.END

    mentor_id_text = update.message.text.strip()
    if not mentor_id_text.isdigit():
        await update.message.reply_text("ID наставника должен быть числом.")
        return MENTOR_ADD

    data = _get_storage(context)
    mentor_id = int(mentor_id_text)
    if mentor_id not in data.mentors:
        data.mentors.append(mentor_id)
        save_data(data)
    await update.message.reply_text(
        "Наставник добавлен.",
        reply_markup=admin_menu_keyboard(),
    )
    return ConversationHandler.END


async def profit_service_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    await query.answer()
    user = update.effective_user
    if not user or user.id not in ADMIN_USER_IDS:
        await _edit_message(query, "Доступ ограничен.")
        return ConversationHandler.END

    _, _, service = query.data.split(":", maxsplit=2)
    context.user_data["profit_service"] = service
    await _edit_message(query, "Введите сумму профита:")
    return PROFIT_AMOUNT


async def handle_profit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    user = update.effective_user
    if not user or user.id not in ADMIN_USER_IDS:
        await update.message.reply_text("Доступ ограничен.")
        return ConversationHandler.END

    amount_text = update.message.text.strip().replace(",", ".")
    try:
        amount_value = float(amount_text)
    except ValueError:
        await update.message.reply_text("Введите корректную сумму.")
        return PROFIT_AMOUNT

    context.user_data["profit_amount"] = amount_value
    await update.message.reply_text(
        "Выберите процент выплаты:",
        reply_markup=profits_rate_keyboard(),
    )
    return PROFIT_RATE


async def profit_rate_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    await query.answer()
    user = update.effective_user
    if not user or user.id not in ADMIN_USER_IDS:
        await _edit_message(query, "Доступ ограничен.")
        return ConversationHandler.END

    _, _, rate_value = query.data.split(":", maxsplit=2)
    context.user_data["profit_rate"] = int(rate_value)
    data = _get_storage(context)
    if data.mentors:
        await _edit_message(
            query,
            "Выберите куратора:",
            reply_markup=profits_curator_keyboard(data.mentors),
        )
    else:
        await _edit_message(
            query,
            "Кураторы не добавлены. Продолжаем без куратора.",
            reply_markup=profits_curator_keyboard([]),
        )
    return PROFIT_MENTOR


async def profit_mentor_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    await query.answer()
    user = update.effective_user
    if not user or user.id not in ADMIN_USER_IDS:
        await _edit_message(query, "Доступ ограничен.")
        return ConversationHandler.END

    _, _, mentor_value = query.data.split(":", maxsplit=2)
    context.user_data["profit_mentor"] = mentor_value
    await _edit_message(
        query,
        "Выберите множитель:",
        reply_markup=profits_multiplier_keyboard(),
    )
    return PROFIT_MULTIPLIER


async def profit_multiplier_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    await query.answer()
    user = update.effective_user
    if not user or user.id not in ADMIN_USER_IDS:
        await _edit_message(query, "Доступ ограничен.")
        return

    _, _, multiplier_value = query.data.split(":", maxsplit=2)
    data = _get_storage(context)
    if not data.profit_channel_id:
        await _edit_message(
            query,
            "Сначала укажите канал профитов.",
            reply_markup=admin_menu_keyboard(),
        )
        return

    profit_message = _build_profit_message(context, multiplier_value)
    await context.bot.send_message(
        chat_id=data.profit_channel_id,
        text=profit_message,
        parse_mode="HTML",
    )
    _apply_profit_payout(context)
    await _edit_message(
        query,
        "Профит отправлен в канал.",
        reply_markup=admin_menu_keyboard(),
    )
    return ConversationHandler.END


async def handle_profit_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    user = update.effective_user
    if not user or user.id not in ADMIN_USER_IDS:
        await update.message.reply_text("Доступ ограничен.")
        return ConversationHandler.END

    channel_text = update.message.text.strip()
    try:
        channel_id = int(channel_text)
    except ValueError:
        await update.message.reply_text("Введите корректный ID канала.")
        return PROFIT_CHANNEL

    data = _get_storage(context)
    data.profit_channel_id = channel_id
    save_data(data)
    await update.message.reply_text(
        "Канал профитов обновлён.",
        reply_markup=admin_menu_keyboard(),
    )
    return ConversationHandler.END


async def handle_balance_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    user = update.effective_user
    if not user or user.id not in ADMIN_USER_IDS:
        await update.message.reply_text("Доступ ограничен.")
        return ConversationHandler.END

    user_id_text = update.message.text.strip()
    if not user_id_text.isdigit():
        await update.message.reply_text("Введите корректный ID пользователя.")
        return BALANCE_USER_ID

    context.user_data["balance_user_id"] = int(user_id_text)
    await update.message.reply_text("Введите сумму для начисления:")
    return BALANCE_AMOUNT


async def handle_balance_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    user = update.effective_user
    if not user or user.id not in ADMIN_USER_IDS:
        await update.message.reply_text("Доступ ограничен.")
        return ConversationHandler.END

    amount_text = update.message.text.strip().replace(",", ".")
    try:
        amount_value = float(amount_text)
    except ValueError:
        await update.message.reply_text("Введите корректную сумму.")
        return BALANCE_AMOUNT

    data = _get_storage(context)
    target_id = context.user_data.get("balance_user_id")
    if not target_id:
        await update.message.reply_text("ID пользователя не найден.")
        return ConversationHandler.END

    profile = ensure_profile(data, target_id)
    profile.balance_rub += int(round(amount_value))
    update_profile(data, profile)
    save_data(data)
    await update.message.reply_text(
        "Баланс обновлён.",
        reply_markup=admin_menu_keyboard(),
    )
    return ConversationHandler.END


def _build_profit_message(context: ContextTypes.DEFAULT_TYPE, multiplier: str) -> str:
    data = _get_storage(context)
    user_id = context.user_data.get("profit_user_id")
    service = context.user_data.get("profit_service")
    amount = context.user_data.get("profit_amount")
    mentor = context.user_data.get("profit_mentor")

    profile_text = "профиль скрыт"
    if user_id:
        profile = ensure_profile(data, int(user_id))
        if profile.show_nickname_in_profits:
            nickname = profile.nickname or f"ID {user_id}"
            profile_text = (
                f"{_format_user_link(int(user_id), nickname)} "
                f"(статус: {profile.status})"
            )

    service_label = {
        "escort": "Escort",
        "trade": "Trade",
        "nft": "NFT",
        "direct": "Прямик",
    }.get(service, "Неизвестно")

    mentor_text = (
        f"Куратор: {_format_user_link(int(mentor), str(mentor))}"
        if mentor and mentor != "none"
        else ""
    )
    return (
        "Воркер: {profile}\n"
        "<b>Сумма</b>: <b><code>{amount}</code></b>\n"
        "<b>Сервис</b>: <b><code>{service}</code></b>\n"
        "{mentor_line}"
        "<b>Множитель</b>: <b>х{multiplier}</b>"
    ).format(
        profile=profile_text,
        amount=_format_amount(amount),
        service=service_label,
        mentor_line=f"{mentor_text}\n" if mentor_text else "",
        multiplier=multiplier,
    )


def _apply_profit_payout(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = _get_storage(context)
    user_id = context.user_data.get("profit_user_id")
    amount = context.user_data.get("profit_amount")
    rate = context.user_data.get("profit_rate")
    if not user_id or amount is None or rate is None:
        return
    amount_value = float(amount)
    payout = int(round(amount_value * (int(rate) / 100)))
    profile = ensure_profile(data, int(user_id))
    profile.balance_rub += payout
    profile.profit_count += 1
    profile.profit_total_rub += int(round(amount_value))
    profile.payout_rate = int(rate)
    profile.profit_history.append(
        {"ts": datetime.now(timezone.utc).isoformat(), "amount": amount_value, "rate": int(rate)}
    )
    update_profile(data, profile)
    data.profit_count += 1
    data.profit_total_rub += int(round(amount_value))
    save_data(data)


def _format_amount(amount: float | int | None) -> str:
    if amount is None:
        return "0"
    if isinstance(amount, float) and amount.is_integer():
        return str(int(amount))
    return str(amount)


async def handle_profit_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    user = update.effective_user
    if not user or user.id not in ADMIN_USER_IDS:
        await update.message.reply_text("Доступ ограничен.")
        return ConversationHandler.END

    user_id_text = update.message.text.strip()
    if not user_id_text.isdigit():
        await update.message.reply_text("Введите корректный ID воркера.")
        return PROFIT_USER_ID

    context.user_data["profit_user_id"] = int(user_id_text)
    await update.message.reply_text(
        "Выберите сервис:",
        reply_markup=profits_service_keyboard(),
    )
    return PROFIT_SERVICE
