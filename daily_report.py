from messages import daily_caption
from telegram_sender import send_message


def send_daily_report(state):
    send_message(daily_caption(state.get("stats", {})))
    # reset daily counters but keep best in state until replaced
    state["stats"] = {"signals": 0, "wins": 0, "losses": 0, "best": state.get("stats", {}).get("best", {})}
