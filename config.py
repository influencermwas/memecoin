import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "45"))
WATCHLIST_SECONDS = int(os.getenv("WATCHLIST_SECONDS", "180"))
MIN_SIGNAL_SCORE = int(os.getenv("MIN_SIGNAL_SCORE", "70"))
GEM_SCORE = int(os.getenv("GEM_SCORE", "90"))
MAX_ALERTS_PER_HOUR = int(os.getenv("MAX_ALERTS_PER_HOUR", "10"))
DEXSCREENER_BASE = os.getenv("DEXSCREENER_BASE", "https://api.dexscreener.com")
RUGCHECK_BASE = os.getenv("RUGCHECK_BASE", "https://api.rugcheck.xyz")
SMART_MONEY_WALLETS = [x.strip() for x in os.getenv("SMART_MONEY_WALLETS", "").split(",") if x.strip()]
BAD_DEV_WALLETS = [x.strip() for x in os.getenv("BAD_DEV_WALLETS", "").split(",") if x.strip()]
DB_FILE = os.getenv("DB_FILE", "bot_state.json")

if not BOT_TOKEN:
    print("WARNING: BOT_TOKEN is empty. Add it to .env")
if not CHANNEL_ID:
    print("WARNING: CHANNEL_ID is empty. Add it to .env")
