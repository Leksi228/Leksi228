import logging
import warnings

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.warnings import PTBUserWarning

from app.config import BOT_TOKEN
from app.handlers import (
    ABOUT,
    BALANCE_AMOUNT,
    BALANCE_USER_ID,
    DESCRIPTION,
    DESIGN_BANNER,
    LINKS_URL,
    MENTOR_ADD,
    NICKNAME,
    ORIGIN,
    PROFIT_CHANNEL,
    PROFIT_USER_ID,
    PROFIT_SERVICE,
    PROFIT_AMOUNT,
    PROFIT_RATE,
    PROFIT_MENTOR,
    PROFIT_MULTIPLIER,
    TIME,
    WITHDRAW_AMOUNT,
    about_action,
    admin_decision,
    admin_menu_action,
    apply_start,
    design_action,
    directions_action,
    handle_about,
    handle_balance_amount,
    handle_balance_user,
    handle_description,
    handle_design_banner,
    handle_links_url,
    handle_mentor_add,
    handle_nickname,
    handle_origin,
    handle_profit_amount,
    handle_profit_channel,
    handle_profit_user_id,
    handle_time,
    handle_withdraw_amount,
    profit_rate_action,
    links_action,
    menu_handler,
    profit_start,
    profit_mentor_action,
    profit_multiplier_action,
    profit_service_action,
    profile_action,
    start,
    withdraw_action,
    wallet_action,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def handle_error(update, context) -> None:
    logger.exception("Ошибка обработки обновления", exc_info=context.error)


def build_application() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is required")

    warnings.filterwarnings(
        "ignore",
        message="If 'per_message=",
        category=PTBUserWarning,
    )

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(CallbackQueryHandler(menu_handler, pattern="^menu:"))

    application.add_handler(
        CallbackQueryHandler(admin_decision, pattern="^admin:(accept|reject):")
    )

    application.add_handler(CallbackQueryHandler(withdraw_action, pattern="^withdraw:"))

    application.add_handler(
        CallbackQueryHandler(directions_action, pattern="^direction:")
    )

    application.add_handler(
        CallbackQueryHandler(about_action, pattern="^about:")
    )

    profile_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(profile_action, pattern="^profile:")],
        states={
            NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_nickname)],
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description)
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(profile_conversation)

    admin_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                admin_menu_action,
                pattern="^admin:(mentor_add|profit_channel|balance_grant|design|links|back)$",
            )
        ],
        states={
            MENTOR_ADD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mentor_add)
            ],
            PROFIT_CHANNEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_profit_channel)
            ],
            BALANCE_USER_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_balance_user)
            ],
            BALANCE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_balance_amount)
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(admin_conversation)

    links_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(links_action, pattern="^links:")],
        states={
            LINKS_URL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_links_url)
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(links_conversation)

    design_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(design_action, pattern="^design:")],
        states={
            DESIGN_BANNER: [
                MessageHandler(filters.PHOTO, handle_design_banner)
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(design_conversation)

    profits_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(profit_start, pattern="^admin:profits$")],
        states={
            PROFIT_USER_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_profit_user_id)
            ],
            PROFIT_SERVICE: [
                CallbackQueryHandler(profit_service_action, pattern="^profit:service:")
            ],
            PROFIT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_profit_amount)
            ],
            PROFIT_RATE: [
                CallbackQueryHandler(profit_rate_action, pattern="^profit:rate:")
            ],
            PROFIT_MENTOR: [
                CallbackQueryHandler(profit_mentor_action, pattern="^profit:mentor:")
            ],
            PROFIT_MULTIPLIER: [
                CallbackQueryHandler(
                    profit_multiplier_action, pattern="^profit:multiplier:"
                )
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(profits_conversation)

    apply_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(apply_start, pattern="^apply:start$")],
        states={
            ORIGIN: [CallbackQueryHandler(handle_origin, pattern="^origin:")],
            TIME: [CallbackQueryHandler(handle_time, pattern="^time:")],
            ABOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_about)],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(apply_conversation)

    wallet_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(wallet_action, pattern="^wallet:")],
        states={
            WITHDRAW_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_withdraw_amount)
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(wallet_conversation)

    application.add_error_handler(handle_error)
    application.run_polling()
файл main
import os

from dotenv import load_dotenv

load_dotenv()

DATA_FILE = os.getenv("DATA_FILE", "data.json")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))
ADMIN_USER_IDS = {
    int(value.strip())
    for value in os.getenv("ADMIN_USER_IDS", "").split(",")
    if value.strip().isdigit()
}
config
handlers 
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

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def _format_amount(amount: float | int) -> str:
    if isinstance(amount, float) and amount.is_integer():
        return str(int(amount))
    return str(amount)


def main_menu_keyboard(is_admin: bool) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("Мой профиль", callback_data="menu:profile"),
            InlineKeyboardButton("Направления", callback_data="menu:tracks"),
        ],
        [
            InlineKeyboardButton("Кураторы", callback_data="menu:mentors"),
            InlineKeyboardButton("О проекте", callback_data="menu:about"),
        ],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton("⚙️ Админка", callback_data="menu:admin")])
    return InlineKeyboardMarkup(rows)


def apply_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Подать заявку", callback_data="apply:start")]]
    )


def origin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Реклама", callback_data="origin:ad"),
                InlineKeyboardButton("Тикток", callback_data="origin:tiktok"),
            ]
        ]
    )


def time_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("4ч", callback_data="time:4h"),
                InlineKeyboardButton("8ч и более", callback_data="time:8h+"),
            ]
        ]
    )


def admin_decision_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Принять", callback_data=f"admin:accept:{user_id}"
                ),
                InlineKeyboardButton(
                    "Отклонить", callback_data=f"admin:reject:{user_id}"
                ),
            ]
        ]
    )


def directions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("💃 Escort", callback_data="direction:escort"),
                InlineKeyboardButton("📈 Trade", callback_data="direction:trade"),
            ],
            [
                InlineKeyboardButton("🖼️ NFT", callback_data="direction:nft"),
                InlineKeyboardButton("⬅️ Назад", callback_data="direction:back"),
            ],
        ]
    )


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎨 Дизайн", callback_data="admin:design"),
                InlineKeyboardButton("🧑‍🏫 Добавить наставника", callback_data="admin:mentor_add"),
            ],
            [
                InlineKeyboardButton("📊 Профиты", callback_data="admin:profits"),
                InlineKeyboardButton("💳 Выдать баланс", callback_data="admin:balance_grant"),
            ],
            [
                InlineKeyboardButton("📣 Канал профитов", callback_data="admin:profit_channel"),
                InlineKeyboardButton("🔗 Ссылки", callback_data="admin:links"),
            ],
            [
                InlineKeyboardButton("⬅️ Назад", callback_data="admin:back"),
            ],
        ]
    )


def design_sections_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Главное меню", callback_data="design:main"),
                InlineKeyboardButton("Направления", callback_data="design:directions"),
            ],
            [
                InlineKeyboardButton("Кураторы", callback_data="design:mentors"),
                InlineKeyboardButton("О проекте", callback_data="design:about"),
            ],
            [
                InlineKeyboardButton("Мой профиль", callback_data="design:profile"),
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="design:back")],
        ]
    )


def links_sections_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("ℹ️ INFO", callback_data="links:info"),
                InlineKeyboardButton("📘 Мануалы", callback_data="links:manuals"),
            ],
            [
                InlineKeyboardButton("💎 Профиты", callback_data="links:profits"),
                InlineKeyboardButton("💬 Чат", callback_data="links:chat"),
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="links:back")],
        ]
    )


def about_links_keyboard(links: dict[str, str]) -> InlineKeyboardMarkup:
    rows = []
    if links.get("info"):
        rows.append([InlineKeyboardButton("ℹ️ INFO", url=links["info"])])
    if links.get("manuals"):
        rows.append([InlineKeyboardButton("📘 Мануалы", url=links["manuals"])])
    if links.get("profits"):
        rows.append([InlineKeyboardButton("💎 Профиты", url=links["profits"])])
    if links.get("chat"):
        rows.append([InlineKeyboardButton("💬 Чат", url=links["chat"])])
    rows.append([InlineKeyboardButton("⬅️ Назад", callback_data="about:back")])
    return InlineKeyboardMarkup(rows) if rows else InlineKeyboardMarkup([])


def profits_service_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("💃 Escort", callback_data="profit:service:escort"),
                InlineKeyboardButton("📈 Trade", callback_data="profit:service:trade"),
            ],
            [
                InlineKeyboardButton("🖼️ NFT", callback_data="profit:service:nft"),
                InlineKeyboardButton("🎯 Прямик", callback_data="profit:service:direct"),
            ],
        ]
    )


def profits_curator_keyboard(mentors: list[int]) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            f"🧑‍🏫 {mentor_id}", callback_data=f"profit:mentor:{mentor_id}"
        )
        for mentor_id in mentors
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    rows.append(
        [InlineKeyboardButton("🙅 Без куратора", callback_data="profit:mentor:none")]
    )
    return InlineKeyboardMarkup(rows)


def profits_multiplier_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for idx in range(1, 11, 2):
        row = [
            InlineKeyboardButton(f"х{idx}", callback_data=f"profit:multiplier:{idx}"),
            InlineKeyboardButton(
                f"х{idx + 1}", callback_data=f"profit:multiplier:{idx + 1}"
            ),
        ]
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def profits_rate_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("80%", callback_data="profit:rate:80"),
                InlineKeyboardButton("70%", callback_data="profit:rate:70"),
            ],
            [
                InlineKeyboardButton("65%", callback_data="profit:rate:65"),
                InlineKeyboardButton("100%", callback_data="profit:rate:100"),
            ],
        ]
    )


def profile_keyboard(show_nickname_in_profits: bool) -> InlineKeyboardMarkup:
    profits_label = "Вкл" if show_nickname_in_profits else "Выкл"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✏️ Никнейм", callback_data="profile:nickname"),
                InlineKeyboardButton("📝 Описание", callback_data="profile:description"),
            ],
            [
                InlineKeyboardButton("👛 Мой кошелек", callback_data="profile:wallet"),
                InlineKeyboardButton(
                    f"📈 Профиты: {profits_label}",
                    callback_data="profile:profits_toggle",
                ),
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="profile:back")],
        ]
    )


def wallet_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("💸 Вывод", callback_data="wallet:withdraw"),
                InlineKeyboardButton(
                    "📜 История транзакций", callback_data="wallet:history"
                ),
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="wallet:back")],
        ]
    )


def withdraw_request_keyboard(user_id: int, amount: float) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Взять в обработку",
                    callback_data=f"withdraw:take:{user_id}:{_format_amount(amount)}",
                )
            ]
        ]
    )
keyboards
storage
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import DATA_FILE


@dataclass
class UserProfile:
    user_id: int
    nickname: Optional[str] = None
    description: Optional[str] = None
    status: str = "обычный"
    show_nickname_in_profits: bool = True
    first_seen: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    balance_rub: int = 0
    profit_count: int = 0
    profit_total_rub: int = 0
    profit_history: List[Dict[str, Any]] = field(default_factory=list)
    payout_rate: int = 0


@dataclass
class BotData:
    approved_users: List[int]
    applications: Dict[str, Dict[str, Any]]
    profiles: Dict[str, Dict[str, Any]]
    mentors: List[int]
    banners: Dict[str, str]
    profit_channel_id: Optional[int]
    links: Dict[str, str]
    profit_count: int
    profit_total_rub: int


def load_data() -> BotData:
    path = Path(DATA_FILE)
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    else:
        raw = {
            "approved_users": [],
            "applications": {},
            "profiles": {},
            "mentors": [],
            "banners": {},
            "profit_channel_id": None,
            "links": {},
            "profit_count": 0,
            "profit_total_rub": 0,
        }
    return BotData(
        approved_users=raw.get("approved_users", []),
        applications=raw.get("applications", {}),
        profiles=raw.get("profiles", {}),
        mentors=raw.get("mentors", []),
        banners=raw.get("banners", {}),
        profit_channel_id=raw.get("profit_channel_id"),
        links=raw.get("links", {}),
        profit_count=raw.get("profit_count", 0),
        profit_total_rub=raw.get("profit_total_rub", 0),
    )


def save_data(data: BotData) -> None:
    payload = {
        "approved_users": data.approved_users,
        "applications": data.applications,
        "profiles": data.profiles,
        "mentors": data.mentors,
        "banners": data.banners,
        "profit_channel_id": data.profit_channel_id,
        "links": data.links,
        "profit_count": data.profit_count,
        "profit_total_rub": data.profit_total_rub,
    }
    path = Path(DATA_FILE)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def ensure_profile(data: BotData, user_id: int) -> UserProfile:
    profile = data.profiles.get(str(user_id))
    if profile:
        default_profile = asdict(UserProfile(user_id=user_id))
        default_profile.update(profile)
        return UserProfile(**default_profile)
    new_profile = UserProfile(user_id=user_id)
    data.profiles[str(user_id)] = asdict(new_profile)
    return new_profile


def update_profile(data: BotData, profile: UserProfile) -> None:
    data.profiles[str(profile.user_id)] = asdict(profile)
это все app

теперь escort
import os
from dotenv import load_dotenv

load_dotenv()

ESCORT_BOT_TOKEN = os.getenv("ESCORT_BOT_TOKEN", "").strip()
ESCORT_DATA_FILE = os.getenv("ESCORT_DATA_FILE", "escort_data.json").strip()
ESCORT_LOG_CHAT_ID = os.getenv("ESCORT_LOG_CHAT_ID", "").strip()
ESCORT_ADMIN_IDS = [
    int(item)
    for item in os.getenv("ESCORT_ADMIN_IDS", "").split(",")
    if item.strip().isdigit()
]
SUPPORT_BOT_TOKEN = os.getenv("SUPPORT_BOT_TOKEN", "").strip()
SUPPORT_LOG_CHAT_ID = os.getenv("SUPPORT_LOG_CHAT_ID", "").strip()
SUPPORT_DATA_FILE = os.getenv("SUPPORT_DATA_FILE", "support_data.json").strip()
config 
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
escort bot.py

from __future__ import annotations

from typing import Dict, List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# ----------------------------
# Helpers
# ----------------------------


def _label(settings: Dict, key: str, default: str) -> str:
    val = settings.get(key)
    return str(val) if val else default


def _sections(settings: Dict) -> List[str]:
    raw = settings.get("menu_sections", [])
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if isinstance(raw, str):
        return [s.strip() for s in raw.split(",") if s.strip()]
    return []


# ----------------------------
# User keyboards
# ----------------------------


def main_menu_keyboard(settings: Dict) -> InlineKeyboardMarkup:
    """Main menu based on settings."""

    sections = set(_sections(settings))

    btn_models = _label(settings, "btn_models", "Модели")
    btn_profile = _label(settings, "btn_profile", "Профиль")
    btn_support = _label(settings, "btn_support", "Поддержка")
    btn_info = _label(settings, "btn_info", "Информация")
    btn_city = _label(settings, "btn_city", "Сменить город")
    btn_inline = _label(settings, "btn_inline_search", "Найти модель")

    keyboard: List[List[InlineKeyboardButton]] = []

    row1: List[InlineKeyboardButton] = []
    if "models" in sections:
        row1.append(InlineKeyboardButton(btn_models, callback_data="menu:models"))
    if "profile" in sections:
        row1.append(InlineKeyboardButton(btn_profile, callback_data="menu:profile"))
    if row1:
        keyboard.append(row1)

    row2: List[InlineKeyboardButton] = []
    if "inline_search" in sections:
        row2.append(InlineKeyboardButton(btn_inline, switch_inline_query_current_chat=""))
    if "support" in sections:
        row2.append(InlineKeyboardButton(btn_support, callback_data="menu:support"))
    if row2:
        keyboard.append(row2)

    row3: List[InlineKeyboardButton] = []
    if "info" in sections:
        row3.append(InlineKeyboardButton(btn_info, callback_data="menu:info"))
    if "city" in sections:
        row3.append(InlineKeyboardButton(btn_city, callback_data="menu:city"))
    if row3:
        keyboard.append(row3)

    if not keyboard:
        keyboard = [[InlineKeyboardButton("Меню", callback_data="menu:models")]]

    return InlineKeyboardMarkup(keyboard)


def profile_keyboard(settings: Dict) -> InlineKeyboardMarkup:
    back = _label(settings, "btn_back", "⬅️ Назад")
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Пополнить баланс", callback_data="profile:topup")],
            [InlineKeyboardButton("Избранное", callback_data="profile:favorites")],
            [InlineKeyboardButton(back, callback_data="profile:back")],
        ]
    )


def topup_keyboard(settings: Dict) -> InlineKeyboardMarkup:
    back = _label(settings, "btn_back", "⬅️ Назад")
    return InlineKeyboardMarkup([[InlineKeyboardButton(back, callback_data="topup:back")]])


def payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Банковская карта", callback_data="pay:card"),
                InlineKeyboardButton("Наличными", callback_data="pay:cash"),
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="topup:back")],
        ]
    )


def models_list_keyboard(
    settings: Dict,
    models: List[tuple[int, Dict]],
    page: int = 0,
    per_page: int = 8,
) -> InlineKeyboardMarkup:
    back = _label(settings, "btn_back", "⬅️ Назад")

    start = page * per_page
    chunk = models[start : start + per_page]

    keyboard: List[List[InlineKeyboardButton]] = []
    for idx, model in chunk:
        name = str(model.get("name") or "Модель")
        keyboard.append([InlineKeyboardButton(name, callback_data=f"model:{idx}")])

    nav: List[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"models:page:{page-1}"))
    if start + per_page < len(models):
        nav.append(InlineKeyboardButton("➡️", callback_data=f"models:page:{page+1}"))
    if nav:
        keyboard.append(nav)

    keyboard.append([InlineKeyboardButton(back, callback_data="models:back")])
    return InlineKeyboardMarkup(keyboard)


def model_detail_keyboard(settings: Dict, link: Optional[str] = None) -> InlineKeyboardMarkup:
    back = _label(settings, "btn_back", "⬅️ Назад")
    keyboard: List[List[InlineKeyboardButton]] = []
    if link and (link.startswith("http://") or link.startswith("https://") or link.startswith("t.me/")):
        url = link
        if url.startswith("t.me/"):
            url = "https://" + url
        keyboard.append([InlineKeyboardButton("🔗 Перейти", url=url)])
    keyboard.append([InlineKeyboardButton(back, callback_data="model:back")])
    return InlineKeyboardMarkup(keyboard)


# ----------------------------
# Admin keyboards
# ----------------------------


def admin_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📦 Модели", callback_data="admin:models"),
                InlineKeyboardButton("🎨 Дизайн", callback_data="admin:design"),
            ],
            [InlineKeyboardButton("❌ Закрыть", callback_data="admin:close")],
        ]
    )


def admin_models_keyboard(models: List[Dict], page: int = 0, per_page: int = 8) -> InlineKeyboardMarkup:
    start = page * per_page
    items = list(enumerate(models))[start : start + per_page]

    keyboard: List[List[InlineKeyboardButton]] = []
    for idx, model in items:
        name = str(model.get("name") or f"Модель #{idx}")
        keyboard.append([InlineKeyboardButton(f"✏️ {name}", callback_data=f"admin:model:{idx}")])

    nav: List[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"admin:models_page:{page-1}"))
    if start + per_page < len(models):
        nav.append(InlineKeyboardButton("➡️", callback_data=f"admin:models_page:{page+1}"))
    if nav:
        keyboard.append(nav)

    keyboard.append([InlineKeyboardButton("➕ Добавить модель", callback_data="admin:model_add")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="admin:back")])
    return InlineKeyboardMarkup(keyboard)


def admin_model_actions_keyboard(model_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Имя", callback_data=f"admin:edit:{model_id}:name"),
                InlineKeyboardButton("Цена", callback_data=f"admin:edit:{model_id}:price"),
            ],
            [
                InlineKeyboardButton("Ссылка", callback_data=f"admin:edit:{model_id}:link"),
                InlineKeyboardButton("Города", callback_data=f"admin:edit:{model_id}:cities"),
            ],
            [InlineKeyboardButton("Описание", callback_data=f"admin:edit:{model_id}:desc")],
            [InlineKeyboardButton("🗑 Удалить", callback_data=f"admin:delete:{model_id}")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin:models")],
        ]
    )


def admin_design_keyboard(settings: Dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Название проекта", callback_data="admin:design_set:title")],
            [InlineKeyboardButton("Ссылка на канал", callback_data="admin:design_set:channel_link")],
            [InlineKeyboardButton("Текст приветствия", callback_data="admin:design_set:welcome_text")],
            [InlineKeyboardButton("Текст меню", callback_data="admin:design_set:menu_text")],
            [InlineKeyboardButton("Юзернейм поддержки", callback_data="admin:design_set:support_username")],
            [InlineKeyboardButton("Подписи кнопок", callback_data="admin:design_buttons")],
            [InlineKeyboardButton("Секция главного меню", callback_data="admin:design_sections")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin:back")],
        ]
    )


def admin_buttons_keyboard(settings: Dict) -> InlineKeyboardMarkup:
    items = [
        ("btn_models", "Кнопка: Модели"),
        ("btn_profile", "Кнопка: Профиль"),
        ("btn_support", "Кнопка: Поддержка"),
        ("btn_info", "Кнопка: Информация"),
        ("btn_city", "Кнопка: Сменить город"),
        ("btn_back", "Кнопка: Назад"),
        ("btn_inline_search", "Кнопка: Инлайн поиск"),
    ]

    keyboard: List[List[InlineKeyboardButton]] = []
    for key, title in items:
        current = str(settings.get(key) or "")
        suffix = f" — <{current}>" if current else ""
        keyboard.append([InlineKeyboardButton(f"{title}{suffix}", callback_data=f"admin:btn_set:{key}")])

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="admin:design")])
    return InlineKeyboardMarkup(keyboard)


def admin_sections_keyboard(settings: Dict) -> InlineKeyboardMarkup:
    current = set(_sections(settings))

    def mark(enabled: bool) -> str:
        return "✅" if enabled else "❌"

    items = [
        ("models", "Модели"),
        ("profile", "Профиль"),
        ("support", "Поддержка"),
        ("info", "Информация"),
        ("city", "Сменить город"),
        ("inline_search", "Инлайн поиск"),
    ]

    keyboard: List[List[InlineKeyboardButton]] = []
    for key, title in items:
        enabled = key in current
        keyboard.append(
            [InlineKeyboardButton(f"{mark(enabled)} {title}", callback_data=f"admin:toggle_section:{key}")]
        )

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="admin:design")])
    return InlineKeyboardMarkup(keyboard)
keyboards

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .config import ESCORT_DATA_FILE


@dataclass
class EscortProfile:
    user_id: int
    username: str = ""
    balance_rub: int = 0
    orders_count: int = 0
    worker_id: Optional[int] = None
    city: str = ""


@dataclass
class EscortData:
    profiles: Dict[str, Dict]
    models: List[Dict]
    settings: Dict[str, str]


DEFAULT_SETTINGS = {
    # тексты
    "title": "Emerans Club",
    "welcome_text": "Привет! Для подбора моделей напишите ваш город.",
    "menu_text": "Главное меню:",
    "support_username": "@EmeransClubSupport_bot",
    "channel_link": "",

    # реквизиты
    "card_number": "",

    # подписи кнопок
    "btn_models": "Модели",
    "btn_profile": "Профиль",
    "btn_support": "Поддержка",
    "btn_info": "Информация",
    "btn_city": "Сменить город",
    "btn_admin": "⚙️ Админка",
    "btn_back": "⬅️ Назад",

    # секции главного меню (что показывать)
    "menu_sections": ["models", "profile", "support", "info", "city"],
}



def ensure_settings(data: "EscortData") -> None:
    """Make sure all required settings exist (migration-safe)."""
    for k, v in DEFAULT_SETTINGS.items():
        if k not in data.settings:
            data.settings[k] = v  # type: ignore[assignment]


def load_data() -> EscortData:
    path = Path(ESCORT_DATA_FILE)
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    else:
        raw = {"profiles": {}, "models": [], "settings": {}}
    data = EscortData(
        profiles=raw.get("profiles", {}),
        models=raw.get("models", []),
        settings=raw.get("settings", {}),
    )
    ensure_settings(data)
    # normalize menu_sections if someone stored it as a string
    if isinstance(data.settings.get("menu_sections"), str):
        data.settings["menu_sections"] = [
            s.strip() for s in str(data.settings.get("menu_sections")).split(",") if s.strip()
        ]
    return data


def save_data(data: EscortData) -> None:
    path = Path(ESCORT_DATA_FILE)
    ensure_settings(data)
    payload = {"profiles": data.profiles, "models": data.models, "settings": data.settings}
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def ensure_profile(data: EscortData, user_id: int, username: str) -> EscortProfile:
    existing = data.profiles.get(str(user_id))
    if existing:
        profile = EscortProfile(**existing)
        if username:
            profile.username = username
        data.profiles[str(user_id)] = asdict(profile)
        return profile
    profile = EscortProfile(user_id=user_id, username=username)
    data.profiles[str(user_id)] = asdict(profile)
    return profile


def update_profile(data: EscortData, profile: EscortProfile) -> None:
    data.profiles[str(profile.user_id)] = asdict(profile)
storage
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from .config import SUPPORT_BOT_TOKEN, SUPPORT_LOG_CHAT_ID
from .support_storage import SupportData, ensure_topic, load_data, save_data

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


SUPPORT_TEXT = (
    "Ваша заявка успешно зарегистрирована ✅\n\n"
    "Вас приветствует служба поддержки.\n\n"
    "⚠️ Для того, чтобы наши менеджеры быстро устранили вашу проблему, Вам следует совершить следующие действия:\n\n"
    "1️⃣  Идентифицируйте Вашу личность, сообщите пользовательский ID, представьтесь.\n\n"
    "2️⃣  Опишите вашу проблему как можно конкретнее.\n\n"
    "3️⃣  Приложите скриншоты, которые связаны с вашей проблемой.\n\n"
    "После того, как Вы создали заявку, ожидайте менеджера, который подключится к вашему чату и поможет Вам устранить проблему.\n\n"
    "⌛️ Среднее время ожидания ответа от поддержки ≈ 1 час.\n\n"
    "С уважением, техническая поддержка."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    user = update.effective_user
    if user:
        if not SUPPORT_LOG_CHAT_ID:
            await update.message.reply_text("SUPPORT_LOG_CHAT_ID не задан.")
            return
        log_text = (
            "Клиент написал /start в поддержку. "
            f"ID: {user.id}, username: @{user.username or 'нет'}"
        )
        try:
            await context.bot.send_message(
                chat_id=int(SUPPORT_LOG_CHAT_ID),
                text=log_text,
            )
        except Exception:
            logger.exception("Не удалось отправить лог в чат поддержки.")

    await update.message.reply_text(SUPPORT_TEXT)


def _get_storage(context: ContextTypes.DEFAULT_TYPE) -> SupportData:
    return context.application.bot_data.setdefault("support_storage", load_data())


async def handle_client_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    user = update.effective_user
    if not user:
        return

    if not SUPPORT_LOG_CHAT_ID:
        await update.message.reply_text("SUPPORT_LOG_CHAT_ID не задан.")
        return

    data = _get_storage(context)
    topic_id = data.user_to_topic.get(str(user.id))
    if not topic_id:
        title = f"{user.first_name or 'Клиент'} | {user.id}"
        if user.username:
            title = f"{user.username} | {user.id}"
        topic = await context.bot.create_forum_topic(
            chat_id=int(SUPPORT_LOG_CHAT_ID),
            name=title,
        )
        topic_id = topic.message_thread_id
        ensure_topic(data, user.id, topic_id)
        save_data(data)

    await context.bot.send_message(
        chat_id=int(SUPPORT_LOG_CHAT_ID),
        message_thread_id=int(topic_id),
        text=(
            f"Сообщение от клиента {user.id} "
            f"(@{user.username or 'нет'}):\n{update.message.text}"
        ),
    )

    if update.message.photo:
        photo = update.message.photo[-1]
        await context.bot.send_photo(
            chat_id=int(SUPPORT_LOG_CHAT_ID),
            message_thread_id=int(topic_id),
            photo=photo.file_id,
            caption=update.message.caption,
        )


async def handle_support_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    if not SUPPORT_LOG_CHAT_ID:
        return

    if update.effective_chat.id != int(SUPPORT_LOG_CHAT_ID):
        return

    if not update.message.is_topic_message:
        return

    thread_id = update.message.message_thread_id
    if not thread_id:
        return

    data = _get_storage(context)
    user_id = data.topic_to_user.get(str(thread_id))
    if not user_id:
        return

    if update.message.text:
        await context.bot.send_message(chat_id=int(user_id), text=update.message.text)
        return

    if update.message.photo:
        photo = update.message.photo[-1]
        await context.bot.send_photo(
            chat_id=int(user_id),
            photo=photo.file_id,
            caption=update.message.caption,
        )


def main() -> None:
    if not SUPPORT_BOT_TOKEN:
        raise RuntimeError("SUPPORT_BOT_TOKEN is required")

    application = ApplicationBuilder().token(SUPPORT_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_client_message)
    )
    application.add_handler(
        MessageHandler(filters.ChatType.SUPERGROUP, handle_support_reply)
    )
    application.run_polling()


if __name__ == "__main__":
    main()
support
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict

from .config import SUPPORT_DATA_FILE


@dataclass
class SupportData:
    user_to_topic: Dict[str, int]
    topic_to_user: Dict[str, int]


def load_data() -> SupportData:
    path = Path(SUPPORT_DATA_FILE)
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    else:
        raw = {"user_to_topic": {}, "topic_to_user": {}}
    return SupportData(
        user_to_topic=raw.get("user_to_topic", {}),
        topic_to_user=raw.get("topic_to_user", {}),
    )


def save_data(data: SupportData) -> None:
    path = Path(SUPPORT_DATA_FILE)
    payload = {
        "user_to_topic": data.user_to_topic,
        "topic_to_user": data.topic_to_user,
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def ensure_topic(data: SupportData, user_id: int, topic_id: int) -> None:
    data.user_to_topic[str(user_id)] = topic_id
    data.topic_to_user[str(topic_id)] = user_id
 support_storage
escort bot

from multiprocessing import Process

from Escort.escort_bot import main as escort_main
from Escort.support_bot import main as support_main
from app.app import build_application


def run_main_bot() -> None:
    build_application()


def run_escort_bot() -> None:
    escort_main()


def run_support_bot() -> None:
    support_main()


if __name__ == "__main__":
    processes = [
        Process(target=run_main_bot),
        Process(target=run_escort_bot),
        Process(target=run_support_bot),
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join()
main

сделай все и помоги мне собрать проект пожалуйста

сделай эскорт бота с инлайн кнопками,админку с инлайн кнопками чтоб я мог добавлять моделей,нужно сделать. Нужно чтоб пользователь ввел город и этот город к нему привязался и не слетал больше. сделать в админке чтоб я мог дизайн ставить через админку!,и выбирать раздел главное меню

убереи фейк криптобота
В эскорт бота нужно убрать ссылку на профиль,добавить цену за час, за 3 часа, ночь,сделать так чтоб можно было добавить фотки моделей через админку. Сделать так чтоб когда модель создалась пользователь ввел свой город и модель была в его городе. Далее админку сделать кнопкой а не командой /admin и в админку добавить еще реквизиты,чтоб админ допустим ввел номер карты и для пользователя который выбирает способ оплаты картой была небольшая анимация текста по типу Создаем счет на оплату анимация и номер карты появляется на 15 минут сделать моноширнным текстом номер карты и чтоб админ еще мог удалять через админку, если номера карты нету то его перенаправляют на тех поддержку,нужно доработать еще тех поддержку чтоб отвечать через топики, позже реализуем кое что,я тебе потом дам zip файл со своим проектом и будем обновлять,спасибо что помогаешь! объясняй весь код пожалуйста

В эскорт бота нужно убрать ссылку на профиль,добавить цену за час, за 3 часа, ночь,сделать так чтоб можно было добавить фотки моделей через админку. Сделать так чтоб когда модель создалась пользователь ввел свой город и модель была в его городе. Далее админку сделать кнопкой а не командой /admin и в админку добавить еще реквизиты,чтоб админ допустим ввел номер карты и для пользователя который выбирает способ оплаты картой была небольшая анимация текста по типу Создаем счет на оплату анимация и номер карты появляется на 15 минут сделать моноширнным текстом номер карты и чтоб админ еще мог удалять через админку, если номера карты нету то его перенаправляют на тех поддержку,нужно доработать еще тех поддержку чтоб отвечать через топики, позже реализуем кое что,я тебе потом дам zip файл со своим проектом и будем обновлять,спасибо что помогаешь! объясняй весь код пожалуйста.
Раздел направления - Escort там есть реферальная ссылка которая создается для воркера в профиле основого бота, сделай там кнопку назад -Мои клиенты(которые привязываются к воркеру и пишут логи действий в самом боте обычного пользователя
