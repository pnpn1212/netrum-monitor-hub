#!/usr/bin/env python3
import os
import asyncio
import requests
from .config import cfg
from .log import run_logs
from .claim import run_auto_claim
from telegram.constants import ParseMode
from datetime import datetime, timedelta
from py_module.daily import send_daily_report
from py_module.language import translations, get_lang, set_lang_file
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

# ---------------- Command Start ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang()
    t = translations.get(lang, translations["en"])
    
    await update.message.reply_text(
        f"✌️ {t.get('welcome')}",
        reply_markup=main_menu_keyboard()
    )

# ---------------- Command /set_lang ----------------
async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = get_lang()
    t = translations.get(lang, translations["en"])

    if query:
        if query.data == "lang":
            try:
                await query.message.delete()
            except:
                pass

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
                [InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi")],
            ])
            await query.message.chat.send_message(
                f"🌐 {t['choose_lang']}",
                reply_markup=keyboard
            )
            return

        elif query.data.startswith("lang_"):
            choice = query.data.replace("lang_", "")
            current_lang = get_lang()

            if choice == current_lang:
                msg = f"⚠️ {t['lang_in_use']}"
                await query.answer(msg, show_alert=True)
                try:
                    await query.message.delete()
                except:
                    pass
                return

            if choice in translations:
                try:
                    await query.message.delete()
                except:
                    pass

                set_lang_file(choice)
                await update_bot_commands(context.bot)
                t_new = translations.get(choice, translations["en"])

                await query.answer(f"✅ {t_new['updated']}")
                await query.message.chat.send_message(
                    f"✅ {t_new['updated']}",
                    reply_markup=main_menu_keyboard()
                )

                await notify(
                    f"✅ {t_new['updated']}",
                    context=context,
                    chat_id=None
                )
            return

    if update.message:
        args = context.args if hasattr(context, "args") else []
        if args:
            choice = args[0].lower()
            current_lang = get_lang()

            if choice == current_lang:
                msg = f"⚠️ {t['lang_in_use']}"
                await update.message.reply_text(msg)
                return

            if choice in translations:
                set_lang_file(choice)
                await update_bot_commands(context.bot)
                t_new = translations.get(choice, translations["en"])
                await update.message.reply_text(
                    f"✅ {t_new['updated']}", 
                    reply_markup=main_menu_keyboard()
                )
                return
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"❌ {t.get('invalid_lang')}"
                )
                return

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
            [InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi")],
        ])
        await update.message.reply_text(
            f"🌐 {t['choose_lang']}", 
            reply_markup=keyboard
        )

# ---------------- Wallet Command ----------------
async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = None

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        try:
            await update.callback_query.message.delete()
        except:
            pass
        await update.callback_query.answer()

    report_msg = send_daily_report()
    if report_msg:
        await context.bot.send_message(
            chat_id=chat_id,
            text=report_msg,
            parse_mode="HTML"
        )

# --- Timeout ---
async def set_timeout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lang = get_lang()
    t = translations.get(lang, translations["en"])
    args = context.args

    if update.callback_query:
        try:
            await update.callback_query.message.delete()
            await update.callback_query.answer()  
        except:
            pass

    old_msg_id = context.user_data.pop('timeout_msg_id', None)
    if old_msg_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=old_msg_id)
        except:
            pass

    if args:
        try:
            value = int(args[0])
            if value < 5 or value > 1440:
                raise ValueError()
        except:
            msg = await context.bot.send_message(chat_id=chat_id, text=f"❌ {t.get('invalid_number')}")
            context.user_data['timeout_msg_id'] = msg.message_id
            return ConversationHandler.END

        current_timeout = int(get_timeout_min())
        if value == current_timeout:
            msg_text = t.get('timeout_already_set').format(value=value)
            msg = await context.bot.send_message(chat_id=chat_id, text=f"⚠️ {msg_text}", parse_mode=ParseMode.HTML)
            context.user_data['timeout_msg_id'] = msg.message_id
            return ConversationHandler.END

        minutes = set_timeout(value)
        await notify(f"✅ {t.get('timeout_updated').format(minutes=minutes)}", context=context, chat_id=chat_id)
        return ConversationHandler.END

    current_timeout = get_timeout_min()
    prompt_text = f"📊 {t.get('current_timeout').format(timeout=current_timeout)}"
    instruction_text = t.get('enter_new_timeout')   

    msg = await context.bot.send_message(
        chat_id=chat_id,
        text=f"<pre>{prompt_text}</pre>\n{instruction_text}",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    context.user_data['timeout_msg_id'] = msg.message_id
    return SET_TIMEOUT

async def set_timeout_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lang = get_lang()
    t = translations.get(lang, translations["en"])

    old_msg_id = context.user_data.pop('timeout_msg_id', None)
    if old_msg_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=old_msg_id)
        except:
            pass

    try:
        value = int(update.message.text.strip())
        if value < 5 or value > 1440:
            raise ValueError()
    except:
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ {t.get('invalid_number')}"
        )
        context.user_data['timeout_msg_id'] = msg.message_id
        return SET_TIMEOUT

    current_timeout = int(get_timeout_min())

    if value == current_timeout:
        msg_text = t.get('timeout_already_set').format(value=value)
        instruction_text = t.get('timeout_prompt_retry')

        keyboard = [[InlineKeyboardButton(f"❌ {t['cancel']}", callback_data="cancel_timeout")]]

        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=f"<pre>⚠️ {msg_text}</pre>\n{instruction_text}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        context.user_data['timeout_msg_id'] = msg.message_id
        return SET_TIMEOUT

    minutes = set_timeout(value)
    await notify(
        f"✅ {t.get('timeout_updated').format(minutes=minutes)}",
        context=context,
        chat_id=chat_id
    )
    return ConversationHandler.END


async def set_timeout_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat.id if query else update.effective_chat.id
    lang = get_lang()
    t = translations.get(lang, translations["en"])

    if query:
        await query.answer()
    
    old_msg_id = context.user_data.pop('timeout_msg_id', None)
    if old_msg_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=old_msg_id)
        except:
            pass

    await context.bot.send_message(chat_id=chat_id, text=f"❌ {t.get('timeout_change_cancelled')}")
    return ConversationHandler.END

# --- Claim ---
async def claim_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang()
    t = translations.get(lang, translations["en"])

    keyboard = [
        [
            InlineKeyboardButton(f"✅ {t['claim_confirm']}", callback_data="claim_confirm"),
            InlineKeyboardButton(f"❌ {t['claim_cancel']}", callback_data="claim_cancel"),
        ]
    ]

    message_text = t["claim_question"]

    if update.callback_query:
        try:
            await update.callback_query.message.delete()
            await update.callback_query.answer()  
        except:
            pass

    if update.message:
        await update.message.reply_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else: 
        chat_id = update.effective_chat.id
        await context.bot.send_message(
            chat_id=chat_id,
            text=message_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def claim_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang()
    t = translations.get(lang, translations["en"])
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except:
        pass

    if query.data == "claim_confirm":
        logs = run_auto_claim()
        if logs:
            await notify(logs, context=context, chat_id=chat_id)
    elif query.data == "claim_cancel":
        await context.bot.send_message(
            chat_id=chat_id, 
            text = f"❌ {t['claim_cancelled']}"
        )

# --- Command handler /logs ---
async def logs_command(update, context):
    if update.callback_query:
        query = update.callback_query
        chat_id = query.message.chat.id
        await query.answer()  
        try:
            await query.message.delete()
        except:
            pass
    elif update.message:
        chat_id = update.message.chat.id

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, run_logs)

# ---------------- Config Helpers ----------------
def cancel_keyboard():
    lang = get_lang()
    t = translations.get(lang, translations["en"])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"❌ {t.get('cancel')}", callback_data="cancel_timeout")]
    ])

def auto_claim_cancel_keyboard():
    lang = get_lang()
    t = translations.get(lang, translations["en"])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"❌ {t.get('cancel')}", callback_data="cancel_auto_claim")]
    ])

# ---------------- Keyboards ----------------
def main_menu_keyboard():
    lang = get_lang() 
    t = translations.get(lang, translations["en"])

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💳 {t['wallet']}", callback_data="wallet_command")],
        [InlineKeyboardButton(f"📜 {t['logs']}", callback_data="logs")],
        [InlineKeyboardButton(f"⏰ {t['timeout']}", callback_data="set_timeout")],
        [InlineKeyboardButton(f"💎 {t['claim']}", callback_data="claim")],
        [InlineKeyboardButton(f"🌐 {t['lang']}", callback_data="lang")],
    ])

# --- Menu callback ---
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data

    if query.data == "set_timeout":
        await set_timeout_command(update, context)
    elif data == "logs":
        await logs_command(update, context)
    elif data == "claim":
        await claim_command(update, context)
    elif data == "wallet_command":
        await wallet_command(update, context)
    elif data == "lang":
        await set_lang(update, context)

def create_telegram_app(TELEGRAM_TOKEN: str, TELEGRAM_CHAT_ID: int) -> ApplicationBuilder:
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    def private_chat_only(handler):
        async def wrapper(update, context):
            if update.effective_chat.id != TELEGRAM_CHAT_ID:
                return
            return await handler(update, context)
        return wrapper

    # --- ConversationHandler set_timeout ---
    conv_timeout = ConversationHandler(
        entry_points=[
            CommandHandler("set_timeout", private_chat_only(set_timeout_command)),
            CallbackQueryHandler(private_chat_only(set_timeout_command), pattern="^set_timeout$")
        ],
        states={
            SET_TIMEOUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_timeout_receive),
                CallbackQueryHandler(set_timeout_cancel, pattern="^cancel_timeout$")
            ]
        },
        fallbacks=[CallbackQueryHandler(set_timeout_cancel, pattern="^cancel_timeout$")],
        allow_reentry=True,
    )

    cancel_handler = CallbackQueryHandler(
        private_chat_only(set_timeout_cancel),
        pattern="^cancel_timeout$"
    )

    # --- Handlers ---
    app.add_handler(CommandHandler("start", private_chat_only(start)))
    app.add_handler(CommandHandler("wallet", private_chat_only(wallet_command)))
    app.add_handler(CommandHandler("logs", private_chat_only(logs_command)))
    app.add_handler(CommandHandler("lang", private_chat_only(set_lang)))
    app.add_handler(conv_timeout)
    app.add_handler(cancel_handler)
    app.add_handler(CommandHandler("claim", private_chat_only(claim_command)))

    # menu_callback lang/claim
    app.add_handler(
        CallbackQueryHandler(
            private_chat_only(menu_callback),
            pattern="^(wallet_command|logs|claim|set_timeout)$"
        )
    )

    # callback claim button
    app.add_handler(CallbackQueryHandler(private_chat_only(claim_button), pattern="^claim_"))

    # callback language
    app.add_handler(CallbackQueryHandler(private_chat_only(set_lang), pattern="^lang$"))   
    app.add_handler(CallbackQueryHandler(private_chat_only(set_lang), pattern="^lang_")) 

    return app, private_chat_only

async def update_bot_commands(bot, retries=3, delay=5):
    lang = get_lang()
    t = translations.get(lang, translations["en"])

    commands_list = [
        ("start", t.get("start_desc", "Show main menu")),
        ("wallet", t.get("wallet_desc", "Check Wallet")),
        ("logs", t.get("logs_desc", "Check Logs Bot")),
        ("set_timeout", t.get("timeout_desc", "Set timeout in minutes")),
        ("claim", t.get("claim_desc", "Claim now")),
        ("lang", t.get("lang_desc", "Set Language")),
    ]

    for attempt in range(1, retries + 1):
        try:
            await bot.set_my_commands([BotCommand(cmd, desc) for cmd, desc in commands_list])
            return commands_list
        except httpx.ConnectTimeout:
            if attempt < retries:
                print(f"[WARN] ConnectTimeout, retrying {attempt}/{retries} in {delay}s...")
                await asyncio.sleep(delay)
            else:
                print("[ERROR] Failed to update bot commands after retries.")
                return []

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

    app, _ = create_telegram_app(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(update_bot_commands(app.bot))

    print("\n💠 Telegram: ✅ ON.")
    return True, app







