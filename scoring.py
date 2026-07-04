from risk_engine import rugcheck, must_pass
from smart_money import smart_money_score
from trend import trend_strength


def score_coin(snapshot):
    rug = rugcheck(snapshot["ca"])
    passed, fails = must_pass(snapshot, rug)
    score = 50

    liq = snapshot.get("liquidity", 0)
    mc = snapshot.get("mc", 0)
    buys = snapshot.get("buys5m", 0)
    sells = snapshot.get("sells5m", 0)
    change = snapshot.get("priceChange5m", 0)
    vol = snapshot.get("volume5m", 0)

    if liq >= 10000: score += 10
    elif liq >= 5000: score += 5
    else: score -= 15

    if mc and 50000 <= mc <= 1500000: score += 8
    if mc > 3000000: score -= 8

    if buys > sells: score += 10
    if buys >= 20: score += 8
    if sells > buys * 1.5: score -= 15

    if 5 <= change <= 80: score += 10
    if change > 200: score -= 18
    if change < -15: score -= 15

    if vol >= 5000: score += 5

    sm_score, sm_count = smart_money_score(snapshot)
    score += sm_score

    if not passed:
        score -= 30

    score = max(0, min(100, int(score)))
    grade = "A+" if score >= 90 else "A" if score >= 80 else "B" if score >= 70 else "C"
    return {
        "score": score,
        "grade": grade,
        "passed": passed,
        "fails": fails,
        "rug": rug,
        "smart_money_count": sm_count,
        "trend": trend_strength(snapshot)
    }
