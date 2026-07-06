import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
WALLETS_FILE = DATA_DIR / "wallets.json"


def _ensure() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not WALLETS_FILE.exists():
        WALLETS_FILE.write_text("{}", encoding="utf-8")


def _load_all() -> Dict[str, Any]:
    _ensure()
    try:
        return json.loads(WALLETS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_all(data: Dict[str, Any]) -> None:
    _ensure()
    tmp = WALLETS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(WALLETS_FILE)


def get_user_record(user_id: int) -> Dict[str, Any]:
    data = _load_all()
    return data.get(str(user_id), {"active_wallet": None, "wallets": []})


def save_user_record(user_id: int, record: Dict[str, Any]) -> None:
    data = _load_all()
    data[str(user_id)] = record
    _save_all(data)


def list_wallets(user_id: int) -> List[Dict[str, Any]]:
    return get_user_record(user_id).get("wallets", [])


def get_active_wallet(user_id: int) -> Optional[Dict[str, Any]]:
    record = get_user_record(user_id)
    active = record.get("active_wallet")
    wallets = record.get("wallets", [])
    if active:
        for wallet in wallets:
            if wallet["label"] == active:
                return wallet
    return wallets[0] if wallets else None


def add_wallet(user_id: int, label: str, public_key: str, encrypted_private_key: str) -> Dict[str, Any]:
    record = get_user_record(user_id)
    wallets = record.setdefault("wallets", [])

    for wallet in wallets:
        if wallet["public_key"] == public_key:
            raise ValueError("This wallet is already imported.")

    wallet = {
        "label": label,
        "public_key": public_key,
        "encrypted_private_key": encrypted_private_key,
        "created_at": int(time.time()),
    }
    wallets.append(wallet)

    if not record.get("active_wallet"):
        record["active_wallet"] = label

    save_user_record(user_id, record)
    return wallet


def set_active_wallet(user_id: int, label: str) -> bool:
    record = get_user_record(user_id)
    for wallet in record.get("wallets", []):
        if wallet["label"] == label:
            record["active_wallet"] = label
            save_user_record(user_id, record)
            return True
    return False


def next_wallet_label(user_id: int) -> str:
    used = {w["label"] for w in list_wallets(user_id)}
    i = 1
    while f"W{i}" in used:
        i += 1
    return f"W{i}"


def delete_wallet(user_id: int, label: str) -> bool:
    record = get_user_record(user_id)
    old_wallets = record.get("wallets", [])
    new_wallets = [w for w in old_wallets if w["label"] != label]
    if len(new_wallets) == len(old_wallets):
        return False

    record["wallets"] = new_wallets
    if record.get("active_wallet") == label:
        record["active_wallet"] = new_wallets[0]["label"] if new_wallets else None

    save_user_record(user_id, record)
    return True
