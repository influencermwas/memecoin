from scanner import fetch_pair
from messages import update_caption, buttons
from telegram_sender import send_photo, send_message
from trend import trend_strength

MILESTONES = [50, 100, 200, 400, 900]


def track_signals(state):
    for ca, sig in list(state.get("signals", {}).items()):
        pair = fetch_pair(ca)
        if not pair:
            continue
        snap = {
            "ca": ca,
            "name": sig.get("name"),
            "symbol": sig.get("symbol"),
            "logo": sig.get("logo"),
            "url": pair.get("url") or sig.get("url"),
            "mc": float(pair.get("marketCap") or pair.get("fdv") or 0),
            "liquidity": float((pair.get("liquidity") or {}).get("usd") or 0),
            "volume5m": float((pair.get("volume") or {}).get("m5") or 0),
            "buys5m": int(((pair.get("txns") or {}).get("m5") or {}).get("buys") or 0),
            "sells5m": int(((pair.get("txns") or {}).get("m5") or {}).get("sells") or 0),
            "priceChange5m": float((pair.get("priceChange") or {}).get("m5") or 0),
        }
        snap["trend"] = trend_strength(snap)
        entry = sig.get("entry_mc") or 0
        if not entry or not snap["mc"]:
            continue
        pnl = ((snap["mc"] - entry) / entry) * 100
        multiple = snap["mc"] / entry
        sent = sig.setdefault("updates_sent", [])

        should_send = None
        if pnl <= -25 and "cutloss" not in sent:
            should_send = "cutloss"
            state["stats"]["losses"] = state["stats"].get("losses", 0) + 1
        else:
            for m in MILESTONES:
                if pnl >= m and str(m) not in sent:
                    should_send = str(m)
                    if m >= 100:
                        state["stats"]["wins"] = state["stats"].get("wins", 0) + 1
                    break
        if should_send:
            caption = update_caption(sig, snap, multiple, pnl)
            if snap.get("logo"):
                send_photo(snap["logo"], caption, buttons(snap))
            else:
                send_message(caption, buttons(snap))
            sent.append(should_send)
            best = state["stats"].setdefault("best", {})
            if multiple > best.get("multiple", 0):
                best.update({"name": sig.get("name"), "multiple": multiple})
