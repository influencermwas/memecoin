import os
import time
from typing import Any, Dict, List, Optional

from price_monitor import get_token_market_data
from positions_storage import get_positions, update_position, close_position
from trading_engine import sell_token_for_sol, get_token_balance_raw
from wallet_manager import decrypt_wallet_key
from wallet_storage import get_user_record


def _entry_price(position: Dict[str, Any]) -> Optional[float]:
    """
    Entry price is saved after first monitor run if missing.
    For best accuracy, next trading upgrade will save exact execution price.
    """
    value = position.get("entry_price_usd")
    try:
        return float(value) if value else None
    except Exception:
        return None


def _profit_percent(entry: float, current: float) -> float:
    if entry <= 0:
        return 0.0
    return ((current - entry) / entry) * 100


async def notify_user(application, user_id: int, text: str) -> None:
    try:
        await application.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
    except Exception:
        pass


def _get_wallet_for_position(user_id: int, position: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    record = get_user_record(user_id)
    wallets = record.get("wallets", [])
    wallet_public_key = position.get("wallet_public_key")

    for wallet in wallets:
        if wallet.get("public_key") == wallet_public_key:
            return wallet

    # fallback to active/first wallet
    active_label = record.get("active_wallet")
    for wallet in wallets:
        if wallet.get("label") == active_label:
            return wallet

    return wallets[0] if wallets else None


async def check_position(application, user_id: int, position: Dict[str, Any]) -> None:
    mint = position.get("mint")
    if not mint or position.get("status") != "open":
        return

    market = get_token_market_data(mint)
    if not market.get("found") or not market.get("price_usd"):
        return

    current_price = float(market["price_usd"])
    entry = _entry_price(position)

    # If entry price was not captured during buy, set it on first monitor check.
    # This means TP/SL starts from first known price after buy.
    if entry is None:
        update_position(user_id, mint, {
            "entry_price_usd": current_price,
            "symbol": market.get("symbol"),
            "name": market.get("name"),
            "last_price_usd": current_price,
            "last_checked_at": int(time.time()),
        })
        await notify_user(
            application,
            user_id,
            "📌 *TP/SL Monitor Started*\n\n"
            f"Token: *{market.get('symbol') or 'Unknown'}*\n"
            f"CA: `{mint}`\n"
            f"Entry price set: `${current_price}`\n\n"
            "Your TP/SL will now use this price as entry.",
        )
        return

    pnl = _profit_percent(entry, current_price)
    tp = position.get("take_profit_pct")
    sl = position.get("stop_loss_pct")

    update_position(user_id, mint, {
        "symbol": market.get("symbol"),
        "name": market.get("name"),
        "last_price_usd": current_price,
        "last_pnl_pct": round(pnl, 2),
        "last_checked_at": int(time.time()),
    })

    should_sell = False
    reason = None

    if tp is not None:
        try:
            if pnl >= float(tp):
                should_sell = True
                reason = f"TP hit +{float(tp):.0f}%"
        except Exception:
            pass

    if not should_sell and sl is not None:
        try:
            if pnl <= -abs(float(sl)):
                should_sell = True
                reason = f"SL hit -{abs(float(sl)):.0f}%"
        except Exception:
            pass

    if not should_sell:
        return

    wallet = _get_wallet_for_position(user_id, position)
    if not wallet:
        await notify_user(application, user_id, f"⚠️ {reason}, but wallet not found for `{mint}`.")
        return

    try:
        raw_balance = get_token_balance_raw(wallet["public_key"], mint)
        if raw_balance <= 0:
            close_position(user_id, mint, {"close_reason": "No token balance"})
            return

        sell_pct = float(os.getenv("TPSL_SELL_PERCENT", "100"))
        sell_amount = int(raw_balance * sell_pct / 100)
        if sell_amount <= 0:
            return

        keypair = decrypt_wallet_key(wallet["encrypted_private_key"])

        result = sell_token_for_sol(
            keypair=keypair,
            token_mint=mint,
            token_amount_raw=sell_amount,
            slippage_bps=int(os.getenv("DEFAULT_SLIPPAGE_BPS", "500")),
        )

        close_position(user_id, mint, {
            "close_reason": reason,
            "sell_signature": result["signature"],
            "exit_price_usd": current_price,
            "final_pnl_pct": round(pnl, 2),
            "auto_sell_percent": sell_pct,
        })

        await notify_user(
            application,
            user_id,
            "✅ *Auto Sell Executed*\n\n"
            f"Reason: *{reason}*\n"
            f"Token: *{market.get('symbol') or 'Unknown'}*\n"
            f"CA: `{mint}`\n"
            f"PnL: *{pnl:.2f}%*\n"
            f"Sold: *{sell_pct:.0f}%*\n"
            f"Estimated SOL out: *{result.get('sol_out_estimate')} SOL*\n"
            f"Tx: `{result['signature']}`",
        )

    except Exception as exc:
        await notify_user(
            application,
            user_id,
            "❌ *Auto Sell Failed*\n\n"
            f"Reason: *{reason}*\n"
            f"Token CA: `{mint}`\n"
            f"Error: `{exc}`",
        )


async def check_all_positions(application) -> None:
    """
    Scans positions.json for all open positions.
    """
    import json
    from pathlib import Path

    data_dir = Path(os.getenv("DATA_DIR", "data"))
    path = data_dir / "positions.json"

    if not path.exists():
        return

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return

    for user_id_text, positions in data.items():
        try:
            user_id = int(user_id_text)
        except Exception:
            continue

        for position in positions:
            if position.get("status") == "open":
                await check_position(application, user_id, position)
