
def trend_strength(snapshot):
    change = snapshot.get("priceChange5m", 0)
    buys = snapshot.get("buys5m", 0)
    sells = snapshot.get("sells5m", 0)
    vol = snapshot.get("volume5m", 0)

    if change > 40 and buys > sells * 2 and vol > 10000:
        return "🔥 Explosive"
    if change > 15 and buys > sells:
        return "📈 Strong Uptrend"
    if change > 0 and buys >= sells:
        return "🟢 Building"
    if change < -20 or sells > buys * 2:
        return "⚠️ Weakening"
    return "➡️ Sideways"
