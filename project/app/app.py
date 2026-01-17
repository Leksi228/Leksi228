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
