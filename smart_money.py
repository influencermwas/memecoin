from config import SMART_MONEY_WALLETS


def smart_money_score(snapshot):
    """Placeholder for wallet tracking. Starts from configured wallet list.
    Real wallet transaction tracking can be added with Helius/Shyft RPC later.
    """
    # Version 1 uses momentum proxy until wallet API is connected.
    buys = snapshot.get("buys5m", 0)
    vol = snapshot.get("volume5m", 0)
    score = 0
    detected = 0
    if buys >= 20 and vol >= 5000:
        score += 12
        detected = min(5, buys // 10)
    elif buys >= 10:
        score += 6
        detected = min(2, buys // 10)
    if SMART_MONEY_WALLETS:
        score += 3
    return score, detected
