#!/usr/bin/env python3
import os
import sys
import warnings
import logging
import tzlocal
from pathlib import Path
from dotenv import load_dotenv

MAIN_FILE = Path(sys.argv[0]).resolve()
CONFIG_PATH = MAIN_FILE.parent / '.netrum'
DAILY_STATS = {'mined': 0.0, 'claims': 0}
tz = tzlocal.get_localzone()

if not CONFIG_PATH.exists():
    print(f"[❌] Not Found File {CONFIG_PATH}")
    sys.exit(1)

load_dotenv(CONFIG_PATH)

possible_paths = [
    Path(os.getenv("NETRUM_NODE_DIR", "")), 
    Path.home() / "netrum-lite-node/src/system/mining",
    Path("/root/netrum-lite-node/src/system/mining"),
    Path("./src/system/mining")
]

NETRUM_NODE_DIR = None
for p in possible_paths:
    if p and p.exists() and (p / "claim.js").exists() and (p / "live-log.js").exists():
        NETRUM_NODE_DIR = p
        break

if NETRUM_NODE_DIR is None:
    raise FileNotFoundError("[❌] claim.js or live-log.js not found: " +
                            ", ".join(str(p) for p in possible_paths if p))

CLAIM_JS = NETRUM_NODE_DIR / "claim.js"
LIVE_LOG_JS = NETRUM_NODE_DIR / "live-log.js"

telegram_token   = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
wallet_address   = os.getenv("WALLET_ADDRESS")
discord_webhook  = os.getenv("DISCORD_WEBHOOK")

required_vars = {
    "TELEGRAM_BOT_TOKEN": telegram_token,
    "TELEGRAM_CHAT_ID": telegram_chat_id,
    "WALLET_ADDRESS": wallet_address,
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    print(f"[❌] Missing variable(s) in {CONFIG_PATH}: {', '.join(missing_vars)}")
    sys.exit(1)

cfg = {
    "TELEGRAM_BOT_TOKEN": telegram_token,
    "TELEGRAM_CHAT_ID": telegram_chat_id,
    "WALLET_ADDRESS": wallet_address,
}

if discord_webhook:
    cfg["DISCORD_WEBHOOK"] = discord_webhook
    

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", module="urllib3")
warnings.filterwarnings("ignore", module="requests")

logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)

logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("discord.http").setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

