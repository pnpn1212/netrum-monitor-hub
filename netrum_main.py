import threading
from py_module.daily import send_daily_report
from py_module.monitor import monitor_log
from py_module.bot import run_telegram_bot 
from py_module.discord import run_discord_bot

def main():
    success, app = run_telegram_bot()
    if not success or not app:
        print("❌ Telegram bot failed to start. Exiting.")
        return 

    threading.Thread(target=monitor_log, daemon=True).start()
    threading.Thread(target=run_discord_bot, daemon=True).start()

    app.run_polling()

if __name__ == '__main__':
    main()
