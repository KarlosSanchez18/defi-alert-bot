#!/usr/bin/env python3
"""
Bot DeFi Alerts (MVP)

- comandos /start /top /help /alerts
- admin: /digest e /checkalerts
"""

import logging
import datetime as dt

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
)

from config import (
    TELEGRAM_TOKEN,
    DEFI_DIGEST_HOUR,
    DEFI_DIGEST_MINUTE,
    ALERT_CHECK_MINUTES,
)

from modules.handlers import (
    start,
    handle_callback_query,
    top_command,
    help_command,
    alerts_command,
    digest_now,
    checkalerts_command,
    send_daily_digest,
    check_defi_alerts,
)

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ============================================================================
# BUILD APPLICATION
# ============================================================================

def build_application() -> Application:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # --------------------
    # Commands
    # --------------------
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("top", top_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("alerts", alerts_command))

    # Admin (dev)
    application.add_handler(CommandHandler("digest", digest_now))
    application.add_handler(CommandHandler("checkalerts", checkalerts_command))

    # --------------------
    # Callbacks (botões)
    # --------------------
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # --------------------
    # Jobs
    # --------------------
    job_queue = application.job_queue

    # Boletim diário (horário do config)
    digest_time = dt.time(DEFI_DIGEST_HOUR, DEFI_DIGEST_MINUTE, 0)
    job_queue.run_daily(
        send_daily_digest,
        time=digest_time,
        days=(0, 1, 2, 3, 4, 5, 6),
        name="daily_defi_digest",
    )
    logger.info(f"✅ Boletim DeFi agendado para {digest_time.strftime('%H:%M')}")

    # Alertas automáticos (a cada X minutos)
    job_queue.run_repeating(
        check_defi_alerts,
        interval=ALERT_CHECK_MINUTES * 60,
        first=60,
        name="defi_alerts_repeating",
    )
    logger.info(f"✅ Alertas DeFi agendados a cada {ALERT_CHECK_MINUTES} minutos")

    # --------------------
    # Error handler
    # --------------------
    async def error_handler(update, context):
        logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)

    application.add_error_handler(error_handler)

    return application


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:
    logger.info("=" * 60)
    logger.info("🤖 BOT DEFI ALERTS (MVP)")
    logger.info("=" * 60)

    if not TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN não configurado em .env")
        return

    application = build_application()
    logger.info("🚀 Bot iniciado. Ctrl+C para parar.")
    application.run_polling(allowed_updates=True)


if __name__ == "__main__":
    main()