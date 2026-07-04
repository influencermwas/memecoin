import json
import os
from datetime import datetime, timezone
from config import DB_FILE

DEFAULT = {
    "seen": {},
    "watchlist": {},
    "signals": {},
    "dev_history": {},
    "stats": {"signals": 0, "wins": 0, "losses": 0, "best": {}}
}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def load_state():
    if not os.path.exists(DB_FILE):
        return DEFAULT.copy()
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in DEFAULT.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return DEFAULT.copy()

def save_state(state):
    tmp = DB_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, DB_FILE)
