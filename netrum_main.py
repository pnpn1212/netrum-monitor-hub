import threading
from threading import Thread, Event
from py_module.daily import send_daily_report
from py_module.monitor import monitor_log
from py_module.bot import run_telegram_bot 
from py_module.discord import run_discord_bot

def main():
    success, app = run_telegram_bot()
    if not success or not app:
        print("❌ Telegram bot failed to start. Exiting.")
        return 

    run_discord_bot() 

    Thread(target=monitor_log, daemon=True).start()

    app.run_polling()

if __name__ == '__main__':
    main()
