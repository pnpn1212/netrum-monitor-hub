#!/usr/bin/env python3
import os
import asyncio
import requests
import httpx
from .config import cfg
from .log import run_logs
from .claim import run_auto_claim
from telegram.constants import ParseMode
from datetime import datetime, timedelta
from py_module.daily import send_daily_report
from py_module.language import translations, get_lang, set_lang_file
from py_module.utils import set_timeout, get_timeout_min, get_timeout_from_file
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, BotCommand, MenuButtonWebApp, WebAppInfo, BotCommandScopeDefault, BotCommandScopeChat
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang()
    t = translations.get(lang, translations["en"])
    
    await update.message.reply_text(
        f"✌️ {t.get('welcome')}",
        reply_markup=main_menu_keyboard()
    )

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
                    f"<pre>✅ {t_new['updated']}</pre>",
                    parse_mode="HTML",
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
        query = update.callback_query
        try:
            await query.message.delete() 
            await query.answer()
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
        await query.message.delete() 
    except:
        pass

    if query.data == "claim_confirm":
        logs = run_auto_claim()
        if logs:
            await notify(logs, context=context, chat_id=chat_id)
    elif query.data == "claim_cancel":
        await context.bot.send_message(
            chat_id=chat_id, 
            text=f"❌ {t['claim_cancelled']}"
        )

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

def cancel_keyboard():
    lang = get_lang()
    t = translations.get(lang, translations["en"])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"❌ {t.get('cancel')}", callback_data="cancel_timeout")]
    ])

def main_menu_keyboard():
    lang = get_lang()
    t = translations.get(lang, translations["en"])
    keyboard = [
        [f"💳 {t['wallet']}", f"📜 {t['logs']}", f"⏰ {t['timeout']}"], 
        [f"💎 {t['claim']}", f"🌐 {t['lang']}"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    TEXT_ACTION_MAP = {
        "💳": "wallet_command",
        "📜": "logs",
        "⏰": "set_timeout",
        "💎": "claim",
        "🌐": "lang"
    }

    data = None

    if query:
        if query.message.chat.type != "private":
            await query.answer()
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text="❌ Commands can only be used in private chat."
            )
            return
        await query.answer()
        data = query.data
        try:
            await query.message.delete()
        except:
            pass

    elif update.message:
        if update.message.chat.type != "private":
            await update.message.reply_text("❌ Commands can only be used in private chat.")
            return
        data = update.message.text

        for key in TEXT_ACTION_MAP:
            if data.startswith(key):
                try:
                    await update.message.delete()
                except:
                    pass
                break

    action = None
    for key, act in TEXT_ACTION_MAP.items():
        if data.startswith(key):
            action = act
            break

    if not action:
        return 

    if action == "set_timeout":
        await set_timeout_command(update, context)
    elif action == "logs":
        await logs_command(update, context)
    elif action == "claim":
        await claim_command(update, context)
    elif action == "wallet_command":
        await wallet_command(update, context)
    elif action == "lang":
        await set_lang(update, context)

def delete_message_before(handler):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message:
            try:
                await update.message.delete()
            except:
                pass

        elif update.callback_query:
            try:
                await update.callback_query.message.delete()
            except:
                pass
        return await handler(update, context)
    return wrapper

def create_telegram_app(TELEGRAM_TOKEN: str, TELEGRAM_CHAT_ID: int):
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.bot._request_kwargs = {"timeout": 60} 

    def private_chat_only(handler):
        async def wrapper(update, context):
            if update.effective_chat.id != TELEGRAM_CHAT_ID:
                return
            return await handler(update, context)
        return wrapper

    conv_timeout = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(menu_callback, pattern="^set_timeout$"),
            CommandHandler("set_timeout", set_timeout_command),
            MessageHandler(filters.TEXT & filters.Regex(r'^⏰'), set_timeout_command)
        ],
        states={
            SET_TIMEOUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, delete_message_before(set_timeout_receive)),
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

    app.add_handler(CommandHandler("start", private_chat_only(start)))
    app.add_handler(CommandHandler("wallet", private_chat_only(wallet_command)))
    app.add_handler(CommandHandler("logs", private_chat_only(logs_command)))
    app.add_handler(CommandHandler("lang", private_chat_only(set_lang)))
    app.add_handler(conv_timeout)
    app.add_handler(cancel_handler)
    app.add_handler(CommandHandler("claim", private_chat_only(claim_command)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, menu_callback))

    app.add_handler(
        CallbackQueryHandler(
            private_chat_only(menu_callback),
            pattern="^(wallet_command|logs|claim|set_timeout)$"
        )
    )

    app.add_handler(CallbackQueryHandler(private_chat_only(claim_button), pattern="^claim_"))
    app.add_handler(CallbackQueryHandler(private_chat_only(set_lang), pattern="^lang$"))   
    app.add_handler(CallbackQueryHandler(private_chat_only(set_lang), pattern="^lang_")) 

    return app, private_chat_only

WEBAPP_URL = "https://netrum.mowvnb.space"

async def update_bot_commands(bot):
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

    await bot.set_my_commands([BotCommand(cmd, desc) for cmd, desc in commands_list])

    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="🌐 Open",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    )


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







