import requests
from config import RUGCHECK_BASE, BAD_DEV_WALLETS


def rugcheck(ca):
    """RugCheck is optional. If endpoint fails, return neutral result."""
    try:
        url = f"{RUGCHECK_BASE}/v1/tokens/{ca}/report/summary"
        data = requests.get(url, timeout=20).json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def must_pass(snapshot, rug=None):
    reasons = []
    liq = snapshot.get("liquidity", 0)
    mc = snapshot.get("mc", 0)
    buys = snapshot.get("buys5m", 0)
    sells = snapshot.get("sells5m", 0)

    if liq < 3000:
        reasons.append("Liquidity too low")
    if mc and liq / mc < 0.01:
        reasons.append("Liquidity/MC ratio weak")
    if buys < 3:
        reasons.append("Not enough buyers yet")
    if sells > buys * 2 and sells > 8:
        reasons.append("Sell pressure too high")

    if rug:
        risk = str(rug.get("riskLevel") or rug.get("score_normalised") or "").lower()
        if "danger" in risk or "high" in risk:
            reasons.append("RugCheck high risk")

    return len(reasons) == 0, reasons
