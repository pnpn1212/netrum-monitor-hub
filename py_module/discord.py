from py_module.config import cfg

def run_discord_bot():
    webhook = cfg.get("DISCORD_WEBHOOK")
    if not webhook:
        print("⚠️  Discord webhook not set, skipping")
        return
    print("🤖 Discord notifications: ✅ ON.")