import os
BOT_USERNAME = os.getenv('BOT_USERNAME', '')
from html import escape
from config import GEM_SCORE


def money(v):
    try:
        if v >= 1_000_000: return f"${v/1_000_000:.2f}M"
        if v >= 1_000: return f"${v/1_000:.1f}K"
        return f"${v:.0f}"
    except Exception:
        return "$0"


def buttons(snapshot):
    rows = []
    ca = snapshot["ca"]

    if BOT_USERNAME:
        rows.append([{
            "text": "🟢 Buy",
            "url": f"https://t.me/{BOT_USERNAME}?start=buy_{ca}"
        }])

    if snapshot.get("url"):
        rows.append([{"text": "📊 Chart", "url": snapshot.get("url")}])

    rows.append([{"text": "🔎 Solscan", "url": f"https://solscan.io/token/{ca}"}])
    return rows


def signal_caption(snapshot, analysis):
    gem = "💎 EXCLUSIVE GEM DETECTED" if analysis["score"] >= GEM_SCORE else "🚀 SOLANA MEMECOIN SIGNAL"
    entry_low = snapshot["mc"] * 0.90
    entry_high = snapshot["mc"] * 1.10
    avoid = snapshot["mc"] * 1.8
    ca = escape(snapshot["ca"])
    return f"""<b>{gem}</b>

<b>{escape(snapshot['name'])} ({escape(snapshot['symbol'])})</b>
CA: <code>{ca}</code>

Score: <b>{analysis['score']}% {analysis['grade']}</b>
Trend: {analysis['trend']}
Smart Money: {analysis['smart_money_count']} wallet signal(s)

Entry MC: <b>{money(snapshot['mc'])}</b>
Entry Zone: {money(entry_low)} – {money(entry_high)}
Avoid Chasing Above: {money(avoid)}
Liquidity: {money(snapshot['liquidity'])}
5m Volume: {money(snapshot['volume5m'])}
5m Buys/Sells: {snapshot['buys5m']} / {snapshot['sells5m']}

🎯 <b>Profit Plan</b>
TP1 +50%: secure small profit.
TP2 2X: take stronger profit, keep moonbag.
TP3 3X+: protect most gains and leave small runner.

🛑 Cut-loss zone: around -25% if momentum breaks.

⚠️ High risk. Not financial advice."""


def update_caption(sig, snapshot, multiple, pnl):
    name = escape(sig.get("name", snapshot.get("name", "Token")))
    entry = sig.get("entry_mc", 0)
    now = snapshot.get("mc", 0)
    if pnl <= -25:
        title = "⚠️ CUT LOSS ALERT"
        body = "Momentum is broken. Protect capital / consider exit."
    elif multiple >= 10:
        title = "🚀 10X UPDATE"
        body = "Huge move. Secure profits and leave only moonbag if holding."
    elif multiple >= 5:
        title = "🔥 5X UPDATE"
        body = "Strong runner. Consider locking major profit."
    elif multiple >= 3:
        title = "🔥 3X UPDATE"
        body = "Excellent move. Protect gains."
    elif multiple >= 2:
        title = "🚀 2X UPDATE"
        body = "Take solid profit and keep moonbag if trend remains strong."
    elif pnl >= 50:
        title = "✅ +50% UPDATE"
        body = "First target reached. Consider taking partial profit."
    else:
        title = "📈 LIVE UPDATE"
        body = "Signal is moving. Keep watching trend and liquidity."
    return f"""<b>{title}</b>

<b>{name}</b>
Called MC: <b>{money(entry)}</b>
Current MC: <b>{money(now)}</b>
PnL: <b>{pnl:.1f}%</b> / <b>{multiple:.2f}X</b>
Trend: {snapshot.get('trend', '')}

{body}"""


def daily_caption(stats):
    signals = stats.get("signals", 0)
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    winrate = (wins / signals * 100) if signals else 0
    best = stats.get("best", {})
    return f"""<b>📊 DAILY RECAP</b>

Signals: {signals}
Wins: {wins}
Losses: {losses}
Win Rate: {winrate:.1f}%

Best Signal: {escape(best.get('name', 'None'))}
Best Move: {best.get('multiple', 0):.2f}X

New signals will continue automatically."""
