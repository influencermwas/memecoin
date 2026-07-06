import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
POSITIONS_FILE = DATA_DIR / "positions.json"
ORDERS_FILE = DATA_DIR / "orders.json"


def _ensure_file(path: Path, default: str = "{}") -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(default, encoding="utf-8")


def _load(path: Path) -> Dict[str, Any]:
    _ensure_file(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save(path: Path, data: Dict[str, Any]) -> None:
    _ensure_file(path)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def get_positions(user_id: int) -> List[Dict[str, Any]]:
    data = _load(POSITIONS_FILE)
    return data.get(str(user_id), [])


def save_position(user_id: int, position: Dict[str, Any]) -> Dict[str, Any]:
    data = _load(POSITIONS_FILE)
    rows = data.setdefault(str(user_id), [])

    position.setdefault("created_at", int(time.time()))
    position.setdefault("status", "open")

    # Merge by mint if position already exists
    for old in rows:
        if old.get("mint") == position.get("mint") and old.get("status") == "open":
            old.update(position)
            _save(POSITIONS_FILE, data)
            return old

    rows.append(position)
    _save(POSITIONS_FILE, data)
    return position


def update_position(user_id: int, mint: str, updates: Dict[str, Any]) -> bool:
    data = _load(POSITIONS_FILE)
    rows = data.get(str(user_id), [])
    for row in rows:
        if row.get("mint") == mint and row.get("status") == "open":
            row.update(updates)
            _save(POSITIONS_FILE, data)
            return True
    return False


def close_position(user_id: int, mint: str, updates: Optional[Dict[str, Any]] = None) -> bool:
    updates = updates or {}
    updates["status"] = "closed"
    updates["closed_at"] = int(time.time())
    return update_position(user_id, mint, updates)


def set_risk_orders(user_id: int, mint: str, take_profit_pct: Optional[float], stop_loss_pct: Optional[float]) -> bool:
    return update_position(user_id, mint, {
        "take_profit_pct": take_profit_pct,
        "stop_loss_pct": stop_loss_pct,
        "risk_updated_at": int(time.time()),
    })
