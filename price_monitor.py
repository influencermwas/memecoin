import time
from typing import Any, Dict, Optional

import requests

DEXSCREENER_TOKEN_URL = "https://api.dexscreener.com/latest/dex/tokens/{mint}"


def get_token_price_usd(mint: str) -> Optional[float]:
    """
    Gets token USD price from DexScreener.
    Returns None if token is not found or price is unavailable.
    """
    try:
        url = DEXSCREENER_TOKEN_URL.format(mint=mint)
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()

        pairs = data.get("pairs") or []
        if not pairs:
            return None

        # Prefer Solana pairs with the highest liquidity
        pairs = [p for p in pairs if (p.get("chainId") or "").lower() == "solana"]
        if not pairs:
            return None

        pairs.sort(key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0), reverse=True)
        price = pairs[0].get("priceUsd")

        return float(price) if price else None
    except Exception:
        return None


def get_token_market_data(mint: str) -> Dict[str, Any]:
    """
    Returns useful token data for positions and TP/SL monitor.
    """
    try:
        url = DEXSCREENER_TOKEN_URL.format(mint=mint)
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()

        pairs = data.get("pairs") or []
        pairs = [p for p in pairs if (p.get("chainId") or "").lower() == "solana"]

        if not pairs:
            return {"found": False, "mint": mint}

        pairs.sort(key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0), reverse=True)
        pair = pairs[0]

        return {
            "found": True,
            "mint": mint,
            "symbol": (pair.get("baseToken") or {}).get("symbol"),
            "name": (pair.get("baseToken") or {}).get("name"),
            "price_usd": float(pair.get("priceUsd") or 0),
            "liquidity_usd": float((pair.get("liquidity") or {}).get("usd") or 0),
            "market_cap": pair.get("marketCap"),
            "fdv": pair.get("fdv"),
            "pair_address": pair.get("pairAddress"),
            "dex_url": pair.get("url"),
            "checked_at": int(time.time()),
        }
    except Exception as exc:
        return {"found": False, "mint": mint, "error": str(exc)}
