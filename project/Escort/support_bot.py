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
