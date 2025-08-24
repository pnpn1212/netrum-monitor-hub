#!/usr/bin/env python3
import os
import asyncio
import requests
from .config import cfg
from .log import run_logs
from .status import run_status
from .claim import run_auto_claim
from telegram.constants import ParseMode
from datetime import datetime, timedelta
from py_module.daily import send_daily_report
from py_module.utils import set_timeout, get_timeout_min, get_timeout_from_file
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)

SET_TIMEOUT = 1
NETRUM_FILE = ".netrum"
AUTO_CLAIM = range(1)

def fmt_dt(dt: datetime) -> str:
    return dt.strftime("%H:%M:%S - %d/%m/%Y")

async def notify(message: str, context=None, chat_id=None, pre: bool = True):
    # Telegram
    if context and chat_id:
        from telegram.constants import ParseMode
        if pre:
            text = f"<pre>{message}</pre>"
            parse_mode = ParseMode.HTML
        else:
            text = message
            parse_mode = None
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode
        )

    # Discord webhook
    webhook = cfg.get("DISCORD_WEBHOOK")
    if webhook:
        try:
            if pre:
                discord_msg = f"```{message}```"
            else:
                discord_msg = message
            requests.post(webhook, json={"content": discord_msg})
        except Exception as e:
            print(f"[❌] Discord webhook failed: {e}")

# ---------------- Keyboards ----------------
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Check Wallet", callback_data="wallet_command")],
        [InlineKeyboardButton("📜 Logs Bot", callback_data="logs")],
        [InlineKeyboardButton("🚨 Status", callback_data="status")],
        [InlineKeyboardButton("⏰ Set Timeout", callback_data="set_timeout")],
        [InlineKeyboardButton("💎 Claim Now", callback_data="claim")],
    ])

def cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_timeout")]])

def auto_claim_cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_auto_claim")]])

async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        await update.callback_query.answer() 

    
    report_msg = send_daily_report() 
    if report_msg:
        await context.bot.send_message(chat_id=chat_id, text=report_msg, parse_mode="HTML")

# ---------------- Command Handlers ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✌️ Welcome! Please choose an action:",
        reply_markup=main_menu_keyboard()
    )

# --- Timeout ---
async def set_timeout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args

    if args:
        try:
            value = int(args[0])
            if value < 5 or value > 1440:
                raise ValueError()
        except:
            await context.bot.send_message(chat_id=chat_id, text="❌ Invalid number, 5-1440.")
            return ConversationHandler.END

        current_timeout = int(get_timeout_min())
        if value == current_timeout:
            msg_text = f"⚠️ Timeout is already set to {value} minutes."
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"<pre>{msg_text}</pre>",
                parse_mode=ParseMode.HTML,
            )
            return ConversationHandler.END

        minutes = set_timeout(value)

        await notify(
            f"✅ Timeout updated to {minutes} minutes",
            context=context, 
            chat_id=chat_id
        )
        return ConversationHandler.END

    msg = await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"<pre>"
            f"📊 Current timeout: {get_timeout_min()} min\n"
            f"</pre>"
            f"Please enter new timeout (5-1440):"
        ),
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    context.user_data['timeout_msg_id'] = msg.message_id
    return SET_TIMEOUT

async def set_timeout_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        value = int(update.message.text.strip())
        if value < 5 or value > 1440:
            raise ValueError()
    except:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Invalid number, 5-1440.",
            reply_markup=cancel_keyboard()
        )
        return SET_TIMEOUT

    current_timeout = int(get_timeout_min())

    if value == current_timeout:
        msg_text = f"⚠️ Timeout is already set to {value} minutes."
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"<pre>{msg_text}</pre>",
            parse_mode=ParseMode.HTML,
            reply_markup=auto_claim_cancel_keyboard()
        )
        return SET_TIMEOUT

    minutes = set_timeout(value)
    msg_id = context.user_data.pop('timeout_msg_id', None)
    if msg_id:
        try:
            await context.bot.edit_message_reply_markup(chat_id=chat_id, message_id=msg_id, reply_markup=None)
        except:
            pass

    await notify(f"✅ Timeout updated to {minutes} minutes", 
                context=context, 
                chat_id=chat_id
    )
    return ConversationHandler.END

async def set_timeout_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id if query else update.effective_chat.id
    if query:
        await query.answer()
        try: await query.edit_message_reply_markup(reply_markup=None)
        except: pass
    await context.bot.send_message(chat_id=chat_id, text="❌ Timeout change cancelled.")
    context.user_data.pop('timeout_msg_id', None)
    return ConversationHandler.END

# --- Claim ---
async def claim_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("✅ Claim", callback_data="claim_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="claim_cancel"),
        ]
    ]
    if update.message:  
        await update.message.reply_text(
            "Do you want to claim?", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif update.callback_query:  
        await update.callback_query.message.reply_text(
            "Do you want to claim?", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def claim_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    try: await query.edit_message_reply_markup(reply_markup=None)
    except: pass

    if query.data == "claim_confirm":
        logs = run_auto_claim()
        if logs: await notify(message, context=context, chat_id=query.message.chat_id)
    elif query.data == "claim_cancel":
        await context.bot.send_message(chat_id=chat_id, text="❌ Claim cancelled.")

# --- Command handler /sync_log ---
async def logs_command(update, context):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, run_logs)

# --- Command handler /status ---
async def status_command(update, context):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, run_status)

# --- Menu callback ---
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data

    if data == "set_timeout":
        return await set_timeout_command(update, context)
    elif data == "logs":
        await logs_command(update, context)
    elif data == "status":
        await status_command(update, context)
    elif data == "claim":
        await claim_command(update, context)
    elif data == "wallet_command":
        await wallet_command(update, context)

def run_telegram_bot() -> tuple[bool, ApplicationBuilder | None]:
    TELEGRAM_TOKEN = cfg.get("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = cfg.get("TELEGRAM_CHAT_ID")

    if not TELEGRAM_TOKEN:
        print("⚠️ Telegram token not set, skipping Telegram bot.")
        return False, None 

    try:
        TELEGRAM_CHAT_ID = int(TELEGRAM_CHAT_ID)
    except (ValueError, TypeError):
        TELEGRAM_CHAT_ID = 0

    if TELEGRAM_CHAT_ID <= 0:
        print(f"❌ TELEGRAM_CHAT_ID ({TELEGRAM_CHAT_ID}) is not a valid personal chat ID.")
        return False, None 

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    def private_chat_only(handler):
        async def wrapper(update, context):
            if update.effective_chat.id != TELEGRAM_CHAT_ID:
                return
            return await handler(update, context)
        return wrapper

    conv_timeout = ConversationHandler(
        entry_points=[CommandHandler("set_timeout", private_chat_only(set_timeout_command))],
        states={
            SET_TIMEOUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, private_chat_only(set_timeout_receive)),
                CallbackQueryHandler(private_chat_only(set_timeout_cancel), pattern="^cancel_timeout$")
            ]
        },
        fallbacks=[CallbackQueryHandler(private_chat_only(set_timeout_cancel), pattern="^cancel_timeout$")],
        allow_reentry=True,
    )

    cancel_handler = CallbackQueryHandler(
        private_chat_only(set_timeout_cancel),
        pattern="^cancel_timeout$"
    )

    app.add_handler(CommandHandler("start", private_chat_only(start)))
    app.add_handler(CommandHandler("wallet", private_chat_only(wallet_command)))
    app.add_handler(CommandHandler("logs", private_chat_only(logs_command)))
    app.add_handler(CommandHandler("status", private_chat_only(status_command)))
    app.add_handler(conv_timeout)
    app.add_handler(cancel_handler)
    app.add_handler(CommandHandler("claim", private_chat_only(claim_command)))
    app.add_handler(CallbackQueryHandler(private_chat_only(menu_callback), pattern="^(wallet_command|logs|status|claim|set_timeout)$"))
    app.add_handler(CallbackQueryHandler(private_chat_only(claim_button), pattern="^claim_"))

    commands = [
        ("start", "Show main menu"),
        ("wallet", "Check Wallet"),
        ("status", "Check Status Node"),
        ("logs", "Check Logs Bot"),
        ("set_timeout", "Set timeout in minutes"),
        ("claim", "Claim now"),
    ]
    asyncio.get_event_loop().run_until_complete(
        app.bot.set_my_commands([BotCommand(cmd, desc) for cmd, desc in commands])
    )

    print("🤖 Telegram bot started.")
    return True, app




