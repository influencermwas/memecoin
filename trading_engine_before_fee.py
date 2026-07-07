import base64
import os
from decimal import Decimal
from typing import Any, Dict, Optional

import requests
from solana.rpc.api import Client
from solana.rpc.types import TokenAccountOpts
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction

SOL_MINT = "So11111111111111111111111111111111111111112"
LAMPORTS_PER_SOL = 1_000_000_000

JUPITER_QUOTE_URL = "https://lite-api.jup.ag/swap/v1/quote"
JUPITER_SWAP_URL = "https://lite-api.jup.ag/swap/v1/swap"


class TradingError(Exception):
    pass


def get_client() -> Client:
    return Client(os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"))


def get_sol_balance(public_key: str) -> float:
    result = get_client().get_balance(Pubkey.from_string(public_key))
    return (result.value or 0) / LAMPORTS_PER_SOL


def sol_to_lamports(sol_amount: float) -> int:
    return int(Decimal(str(sol_amount)) * LAMPORTS_PER_SOL)


def get_quote(
    input_mint: str,
    output_mint: str,
    amount: int,
    slippage_bps: int = 500,
) -> Dict[str, Any]:
    params = {
        "inputMint": input_mint,
        "outputMint": output_mint,
        "amount": str(amount),
        "slippageBps": str(slippage_bps),
        "onlyDirectRoutes": "false",
    }
    r = requests.get(JUPITER_QUOTE_URL, params=params, timeout=20)
    if r.status_code != 200:
        raise TradingError(f"Quote failed: {r.text[:300]}")
    data = r.json()
    if not data:
        raise TradingError("No route found for this token.")
    return data


def build_swap_transaction(
    quote_response: Dict[str, Any],
    user_public_key: str,
    priority_fee_lamports: Optional[int] = None,
) -> str:
    payload = {
        "quoteResponse": quote_response,
        "userPublicKey": user_public_key,
        "wrapAndUnwrapSol": True,
        "dynamicComputeUnitLimit": True,
    }

    if priority_fee_lamports:
        payload["prioritizationFeeLamports"] = priority_fee_lamports
    else:
        payload["prioritizationFeeLamports"] = "auto"

    r = requests.post(JUPITER_SWAP_URL, json=payload, timeout=30)
    if r.status_code != 200:
        raise TradingError(f"Swap build failed: {r.text[:300]}")
    data = r.json()
    tx = data.get("swapTransaction")
    if not tx:
        raise TradingError(f"No swap transaction returned: {data}")
    return tx


def sign_and_send_swap(swap_transaction_b64: str, keypair: Keypair) -> str:
    raw_tx = base64.b64decode(swap_transaction_b64)
    tx = VersionedTransaction.from_bytes(raw_tx)

    signed_tx = VersionedTransaction(tx.message, [keypair])
    result = get_client().send_raw_transaction(bytes(signed_tx))

    signature = str(result.value)
    if not signature:
        raise TradingError("Transaction was not sent.")
    return signature


def buy_token_with_sol(
    keypair: Keypair,
    token_mint: str,
    sol_amount: float,
    slippage_bps: int = 500,
) -> Dict[str, Any]:
    public_key = str(keypair.pubkey())
    lamports = sol_to_lamports(sol_amount)

    quote = get_quote(SOL_MINT, token_mint, lamports, slippage_bps)
    swap_tx = build_swap_transaction(quote, public_key)
    signature = sign_and_send_swap(swap_tx, keypair)

    return {
        "signature": signature,
        "input_mint": SOL_MINT,
        "output_mint": token_mint,
        "sol_spent": sol_amount,
        "raw_in_amount": quote.get("inAmount"),
        "raw_out_amount": quote.get("outAmount"),
        "price_impact_pct": quote.get("priceImpactPct"),
        "quote": quote,
    }


def sell_token_for_sol(
    keypair: Keypair,
    token_mint: str,
    token_amount_raw: int,
    slippage_bps: int = 500,
) -> Dict[str, Any]:
    public_key = str(keypair.pubkey())

    quote = get_quote(token_mint, SOL_MINT, token_amount_raw, slippage_bps)
    swap_tx = build_swap_transaction(quote, public_key)
    signature = sign_and_send_swap(swap_tx, keypair)

    return {
        "signature": signature,
        "input_mint": token_mint,
        "output_mint": SOL_MINT,
        "raw_in_amount": quote.get("inAmount"),
        "raw_out_amount": quote.get("outAmount"),
        "sol_out_estimate": int(quote.get("outAmount", 0)) / LAMPORTS_PER_SOL,
        "price_impact_pct": quote.get("priceImpactPct"),
        "quote": quote,
    }


def get_token_balance_raw(owner_public_key: str, mint: str) -> int:
    client = get_client()
    resp = client.get_token_accounts_by_owner_json_parsed(
        Pubkey.from_string(owner_public_key),
        TokenAccountOpts(mint=Pubkey.from_string(mint))
    )

    total = 0
    for item in resp.value or []:
        amount_info = item.account.data.parsed["info"]["tokenAmount"]
        total += int(amount_info["amount"])
    return total



def percent_of_wallet_sol(public_key: str, percent: float, keep_fee_sol: float = 0.01) -> float:
    balance = get_sol_balance(public_key)
    usable = max(balance - keep_fee_sol, 0)
    return round(usable * (percent / 100), 9)
