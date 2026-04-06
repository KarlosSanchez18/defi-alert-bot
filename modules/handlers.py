"""
Handlers do Bot (MVP DeFi)

- /start + menu
- /top /help /alerts
- boletim diário (send_daily_digest)
- alertas automáticos (check_defi_alerts)
- comandos admin (/digest e /checkalerts)
"""

import logging
import asyncio
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from storage.subscribers import is_subscriber

from config import (
    ADMIN_USER_IDS,
    DEFI_TOP_LIMIT,
    APY_JUMP_MIN,
    CHECKOUT_API_URL,
)

from services.defillama import top_pools
from storage.users import add_user, list_users
from storage.defi_alerts import load_snapshot, save_snapshot, build_snapshot, diff_pools

logger = logging.getLogger(__name__)

MENU = 0
_defi_alerts_lock = asyncio.Lock()


# ==============================================================================
# helpers
# ==============================================================================

def is_admin(update: Update) -> bool:
    return bool(update.effective_user and (update.effective_user.id in ADMIN_USER_IDS))


def _format_top_pools_message(pools) -> str:
    msg = ""
    for pool in pools:
        chain = pool.get("chain") or "N/A"
        project = pool.get("project") or "N/A"
        symbol = pool.get("symbol") or "N/A"
        apy = float(pool.get("apy") or 0)
        tvl = float(pool.get("tvlUsd") or 0)

        msg += (
            f"💰 *{symbol}*\n"
            f"🧠 Protocol: {project}\n"
            f"⛓️ Chain: {chain}\n"
            f"📈 APY: {apy:.2f}%\n"
            f"💧 TVL: ${tvl:,.0f}\n\n"
        )
    return msg


def _create_checkout_url(user_id: int, chat_id: int) -> str | None:
    try:
        response = requests.post(
            f"{CHECKOUT_API_URL}/create-checkout-session",
            json={
                "telegram_user_id": user_id,
                "chat_id": chat_id,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("url") or data.get("checkout_url")
    except Exception as e:
        logger.warning(f"Falha ao criar checkout session: {e}")
        return None


async def _send_checkout_message(update: Update, message_prefix: str) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    checkout_url = _create_checkout_url(user_id, chat_id)

    if not checkout_url:
        fallback_message = (
            f"{message_prefix}\n\n"
            "⚠️ Payment link is temporarily unavailable.\n"
            "Please try again in a moment."
        )

        if update.message:
            await update.message.reply_text(fallback_message)
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(fallback_message)
        return

    keyboard = [
        [InlineKeyboardButton("💳 Unlock access", url=checkout_url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    final_message = (
        f"{message_prefix}\n\n"
        "Tap the button below to complete your subscription."
    )

    if update.message:
        await update.message.reply_text(
            final_message,
            reply_markup=reply_markup
        )
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            final_message,
            reply_markup=reply_markup
        )


async def require_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id

    if is_subscriber(user_id):
        return True

    await _send_checkout_message(
        update,
        "🔒 Premium feature.\n\nSubscribe to unlock full access to Top Pools, alerts, and daily digest."
    )
    return False


# ==============================================================================
# /start + menu
# ==============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    chat_id = update.effective_chat.id

    add_user(user.id, chat_id)

    welcome_msg = (
        "🚀 DeFi Alerts Bot\n\n"
        "Get real-time DeFi opportunities directly on Telegram.\n\n"
        "💡 What you get:\n"
        "• High APY pools\n"
        "• New opportunities alerts\n"
        "• APY spike detection\n"
        "• Daily summary\n\n"
        "👇 Use the buttons below or /top /alerts /help"
    )

    keyboard = [
        [InlineKeyboardButton("🔥 Top Pools", callback_data="defi_top")],
        [InlineKeyboardButton("🚨 Alerts", callback_data="defi_alerts")],
        [InlineKeyboardButton("❓ Help", callback_data="defi_help")],
    ]

    await update.message.reply_text(
        welcome_msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return MENU


# ==============================================================================
# Top Pools (botão + /top)
# ==============================================================================

async def top_defi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_subscription(update, context):
        return

    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔄 Fetching top DeFi pools...")

    try:
        pools = top_pools(DEFI_TOP_LIMIT)
        msg = "🔥 *Top DeFi Pools*\n\n" + _format_top_pools_message(pools)
        await query.edit_message_text(msg, parse_mode="Markdown")
    except Exception as e:
        await query.edit_message_text(f"❌ Error fetching pools: {e}")


async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_subscription(update, context):
        return

    await update.message.reply_text("🔄 Fetching top DeFi pools...")

    try:
        pools = top_pools(DEFI_TOP_LIMIT)
        msg = "🔥 *Top DeFi Pools*\n\n" + _format_top_pools_message(pools)
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching pools: {e}")


# ==============================================================================
# /help e /alerts
# ==============================================================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "❓ Help\n\n"
        "Available commands:\n"
        "/start - Open the main menu\n"
        "/top - View premium top DeFi pools\n"
        "/alerts - See what subscribers receive\n"
        "/help - Show this help message\n\n"
        "Premium subscribers receive:\n"
        "• Top DeFi pools\n"
        "• Alerts every 15 minutes\n"
        "• New opportunity detection\n"
        "• APY jump alerts\n"
        "• Daily digest at 9:00"
    )

    await update.message.reply_text(text)


async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if not is_subscriber(user_id):
        await _send_checkout_message(
            update,
            "🚨 DeFi Alerts\n\n"
            "The bot monitors DeFi opportunities and sends updates directly on Telegram.\n\n"
            "Subscribers get:\n"
            "• Checks every 15 minutes\n"
            "• New high APY opportunities\n"
            "• Strong APY jump alerts\n"
            "• Daily digest at 9:00\n\n"
            "Full alerts are available only for subscribers."
        )
        return

    await update.message.reply_text("🔄 Checking latest DeFi alerts...")

    try:
        pools = top_pools(DEFI_TOP_LIMIT)
        old_snapshot = load_snapshot()
        new_pools, apy_jumps = diff_pools(pools, old_snapshot, apy_jump_min=APY_JUMP_MIN)

        if not new_pools and not apy_jumps:
            await update.message.reply_text(
                "✅ No new DeFi alerts right now.\n\n"
                "No new pools entered the top and no strong APY jumps were detected."
            )
            return

        message = "🚨 *Latest DeFi Alerts*\n\n"

        if new_pools:
            message += "🆕 *New pools in the top:*\n"
            for p in new_pools[:5]:
                message += (
                    f"- {p.get('symbol')} | {p.get('project')} | {p.get('chain')} "
                    f"| APY {float(p.get('apy') or 0):.2f}%\n"
                )
            message += "\n"

        if apy_jumps:
            message += "📈 *Strong APY jumps:*\n"
            for p, old_apy, new_apy in apy_jumps[:5]:
                message += (
                    f"- {p.get('symbol')} | {p.get('project')} | {p.get('chain')} "
                    f"| {old_apy:.2f}% → {new_apy:.2f}%\n"
                )

        await update.message.reply_text(message, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Error checking alerts: {e}")


# ==============================================================================
# Alertas automáticos (chamado pelo job_queue) + /checkalerts admin
# ==============================================================================

async def check_defi_alerts(context: ContextTypes.DEFAULT_TYPE) -> None:
    if _defi_alerts_lock.locked():
        return

    async with _defi_alerts_lock:
        users = list_users()
        if not users:
            return

        try:
            pools = top_pools(DEFI_TOP_LIMIT)

            old_snapshot = load_snapshot()
            new_pools, apy_jumps = diff_pools(pools, old_snapshot, apy_jump_min=APY_JUMP_MIN)

            if not new_pools and not apy_jumps:
                save_snapshot(build_snapshot(pools))
                return

            message = "🚨 *New DeFi opportunity detected*\n\n"

            if new_pools:
                message += "🆕 *New pool in the top*\n"
                for p in new_pools[:3]:
                    message += (
                        f"- {p.get('symbol')} | {p.get('project')} | "
                        f"APY {float(p.get('apy') or 0):.2f}%\n"
                    )
                message += "\n"

            if apy_jumps:
                message += "📈 *Strong APY jump*\n"
                for p, old_apy, new_apy in apy_jumps[:3]:
                    message += f"- {p.get('symbol')} {old_apy:.2f}% → {new_apy:.2f}%\n"

            for u in users:
                user_id = u.get("telegram_user_id")
                if not is_subscriber(user_id):
                    continue

                chat_id = u.get("chat_id")
                if not chat_id:
                    continue

                try:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.warning(f"Falha ao enviar alerta para chat_id={chat_id}: {e}")

            save_snapshot(build_snapshot(pools))

        except Exception as e:
            logger.error(f"Erro ao checar alertas DeFi: {e}", exc_info=True)


async def checkalerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        await update.message.reply_text("❌ Command available only for admin.")
        return

    await update.message.reply_text("🔎 Checking alerts now...")
    await check_defi_alerts(context)
    await update.message.reply_text("✅ Check finished.")


# ==============================================================================
# Boletim diário (chamado pelo job_queue) + /digest admin
# ==============================================================================

async def send_daily_digest(context: ContextTypes.DEFAULT_TYPE) -> None:
    users = list_users()
    if not users:
        return

    try:
        pools = top_pools(DEFI_TOP_LIMIT)

        old_snapshot = load_snapshot()
        new_pools, apy_jumps = diff_pools(pools, old_snapshot, apy_jump_min=APY_JUMP_MIN)
        new_snapshot = build_snapshot(pools)

        message = "📰 *Daily Digest — Top DeFi Pools*\n\n"

        if new_pools or apy_jumps:
            message += "🚨 *Changes since the last snapshot:*\n\n"

            if new_pools:
                message += "🆕 *New pools in the top:*\n"
                for p in new_pools[:3]:
                    message += (
                        f"- {p.get('symbol')} | {p.get('project')} | {p.get('chain')} "
                        f"| APY {float(p.get('apy') or 0):.2f}%\n"
                    )
                message += "\n"

            if apy_jumps:
                message += "📈 *Strong APY jump:*\n"
                for p, old_apy, new_apy in apy_jumps[:3]:
                    message += (
                        f"- {p.get('symbol')} | {p.get('project')} | {p.get('chain')} "
                        f"| {old_apy:.2f}% → {new_apy:.2f}%\n"
                    )
                message += "\n"

        message += "🔥 *Top Pools (now):*\n\n"
        message += _format_top_pools_message(pools)

        for u in users:
            user_id = u.get("telegram_user_id")
            if not is_subscriber(user_id):
                continue

            chat_id = u.get("chat_id")
            if not chat_id:
                continue

            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.warning(f"Falha ao enviar boletim para chat_id={chat_id}: {e}")

        save_snapshot(new_snapshot)

    except Exception as e:
        logger.error(f"Erro no boletim diário: {e}", exc_info=True)


async def digest_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        await update.message.reply_text("❌ Command available only for admin.")
        return

    await update.message.reply_text("🔄 Sending digest now...")
    await send_daily_digest(context)
    await update.message.reply_text("✅ Digest sent.")


# ==============================================================================
# CALLBACK DOS BOTÕES
# ==============================================================================

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "defi_top":
        await top_defi(update, context)

    elif query.data == "defi_alerts":
        user_id = update.effective_user.id

        if not is_subscriber(user_id):
            await _send_checkout_message(
                update,
                "🚨 DeFi Alerts\n\n"
                "The bot monitors DeFi opportunities and sends updates directly on Telegram.\n\n"
                "Subscribers get:\n"
                "• Checks every 15 minutes\n"
                "• New high APY opportunities\n"
                "• Strong APY jump alerts\n"
                "• Daily digest at 9:00\n\n"
                "Full alerts are available only for subscribers."
            )
        else:
            await query.edit_message_text("🔄 Checking latest DeFi alerts...")

            try:
                pools = top_pools(DEFI_TOP_LIMIT)
                old_snapshot = load_snapshot()
                new_pools, apy_jumps = diff_pools(pools, old_snapshot, apy_jump_min=APY_JUMP_MIN)

                if not new_pools and not apy_jumps:
                    await query.edit_message_text(
                        "✅ No new DeFi alerts right now.\n\n"
                        "No new pools entered the top and no strong APY jumps were detected."
                    )
                else:
                    message = "🚨 *Latest DeFi Alerts*\n\n"

                    if new_pools:
                        message += "🆕 *New pools in the top:*\n"
                        for p in new_pools[:5]:
                            message += (
                                f"- {p.get('symbol')} | {p.get('project')} | {p.get('chain')} "
                                f"| APY {float(p.get('apy') or 0):.2f}%\n"
                            )
                        message += "\n"

                    if apy_jumps:
                        message += "📈 *Strong APY jumps:*\n"
                        for p, old_apy, new_apy in apy_jumps[:5]:
                            message += (
                                f"- {p.get('symbol')} | {p.get('project')} | {p.get('chain')} "
                                f"| {old_apy:.2f}% → {new_apy:.2f}%\n"
                            )

                    await query.edit_message_text(message, parse_mode="Markdown")

            except Exception as e:
                await query.edit_message_text(f"❌ Error checking alerts: {e}")

    elif query.data == "defi_help":
        await query.edit_message_text(
            "❓ Help\n\n"
            "Available commands:\n"
            "/start - Open the main menu\n"
            "/top - View premium top DeFi pools\n"
            "/alerts - See what subscribers receive\n"
            "/help - Show this help message\n\n"
            "Premium subscribers receive:\n"
            "• Top DeFi pools\n"
            "• Alerts every 15 minutes\n"
            "• New opportunity detection\n"
            "• APY jump alerts\n"
            "• Daily digest at 9:00"
        )

    return MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END