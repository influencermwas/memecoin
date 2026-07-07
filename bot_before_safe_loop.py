import time
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler

from config import SCAN_INTERVAL_SECONDS, WATCHLIST_SECONDS, MIN_SIGNAL_SCORE
from storage import load_state, save_state, now_iso
from scanner import fetch_latest_solana_profiles, coin_snapshot
from scoring import score_coin
from messages import signal_caption, buttons
from telegram_sender import send_photo, send_message
from tracker import track_signals
from daily_report import send_daily_report


def age_seconds(iso):
    try:
        return (datetime.now(timezone.utc) - datetime.fromisoformat(iso)).total_seconds()
    except Exception:
        return 0


def scan_once():
    state = load_state()

    # 1. detect new coins and add silent watchlist
    profiles = fetch_latest_solana_profiles()
    for p in profiles:
        ca = p["ca"]
        if ca in state["seen"] or ca in state["watchlist"] or ca in state["signals"]:
            continue
        snap = coin_snapshot(p)
        if not snap:
            continue
        analysis = score_coin(snap)
        state["watchlist"][ca] = {"first_seen": now_iso(), "snapshot": snap, "best_score": analysis["score"]}
        state["seen"][ca] = now_iso()

    # 2. after silent watch period, score and broadcast only qualifying coins
    for ca, item in list(state["watchlist"].items()):
        if age_seconds(item["first_seen"]) < WATCHLIST_SECONDS:
            continue
        snap = coin_snapshot({"ca": ca, "name": item["snapshot"].get("name"), "logo": item["snapshot"].get("logo"), "url": item["snapshot"].get("url")})
        if not snap:
            del state["watchlist"][ca]
            continue
        analysis = score_coin(snap)
        if analysis["score"] >= MIN_SIGNAL_SCORE and analysis["passed"]:
            caption = signal_caption(snap, analysis)
            if snap.get("logo"):
                send_photo(snap["logo"], caption, buttons(snap))
            else:
                send_message(caption, buttons(snap))
            state["signals"][ca] = {
                "name": snap["name"], "symbol": snap["symbol"], "logo": snap.get("logo"),
                "url": snap.get("url"), "entry_mc": snap.get("mc"), "sent_at": now_iso(),
                "score": analysis["score"], "updates_sent": []
            }
            state["stats"]["signals"] = state["stats"].get("signals", 0) + 1
        del state["watchlist"][ca]

    # 3. live updates for already posted signals
    track_signals(state)
    save_state(state)


def report_job():
    state = load_state()
    send_daily_report(state)
    save_state(state)


def main():
    print("Solana memecoin channel bot started...")
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(scan_once, "interval", seconds=SCAN_INTERVAL_SECONDS, max_instances=1)
    scheduler.add_job(report_job, "cron", hour=0, minute=0)
    scheduler.start()
    scan_once()
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
