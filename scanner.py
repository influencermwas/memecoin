import time
import requests
from config import DEXSCREENER_BASE


def fetch_latest_solana_profiles(limit=30):
    """Fetch latest token profiles and keep Solana tokens only."""
    url = f"{DEXSCREENER_BASE}/token-profiles/latest/v1"
    try:
        data = requests.get(url, timeout=20).json()
    except Exception:
        return []
    results = []
    for item in data[:limit] if isinstance(data, list) else []:
        if item.get("chainId") == "solana" and item.get("tokenAddress"):
            results.append({
                "ca": item.get("tokenAddress"),
                "name": item.get("description") or item.get("tokenAddress")[:6],
                "logo": item.get("icon"),
                "links": item.get("links") or [],
                "url": item.get("url")
            })
    return results


def fetch_pair(ca):
    url = f"{DEXSCREENER_BASE}/latest/dex/tokens/{ca}"
    try:
        data = requests.get(url, timeout=20).json()
    except Exception:
        return None
    pairs = [p for p in (data.get("pairs") or []) if p.get("chainId") == "solana"]
    if not pairs:
        return None
    pairs.sort(key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0), reverse=True)
    return pairs[0]


def coin_snapshot(profile):
    pair = fetch_pair(profile["ca"])
    if not pair:
        return None
    base = pair.get("baseToken", {})
    info = pair.get("info", {}) or {}
    return {
        "ca": profile["ca"],
        "name": base.get("name") or profile.get("name") or "Unknown",
        "symbol": base.get("symbol") or "?",
        "logo": profile.get("logo") or info.get("imageUrl"),
        "url": pair.get("url") or profile.get("url"),
        "pair": pair.get("pairAddress"),
        "priceUsd": float(pair.get("priceUsd") or 0),
        "mc": float(pair.get("marketCap") or pair.get("fdv") or 0),
        "liquidity": float((pair.get("liquidity") or {}).get("usd") or 0),
        "volume5m": float((pair.get("volume") or {}).get("m5") or 0),
        "volume1h": float((pair.get("volume") or {}).get("h1") or 0),
        "buys5m": int(((pair.get("txns") or {}).get("m5") or {}).get("buys") or 0),
        "sells5m": int(((pair.get("txns") or {}).get("m5") or {}).get("sells") or 0),
        "priceChange5m": float((pair.get("priceChange") or {}).get("m5") or 0),
        "createdAt": int(pair.get("pairCreatedAt") or time.time() * 1000),
    }
