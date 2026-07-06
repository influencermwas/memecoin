import json
from typing import Tuple

import base58
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client

from security import encrypt_text, decrypt_text


def normalize_private_key(raw: str) -> bytes:
    """
    Accepts common Phantom/Solflare exports:
    - base58 private key string
    - JSON array like [12,34,...]
    """
    raw = raw.strip()

    if raw.startswith("[") and raw.endswith("]"):
        arr = json.loads(raw)
        if not isinstance(arr, list):
            raise ValueError("Invalid JSON private key.")
        key_bytes = bytes(arr)
    else:
        key_bytes = base58.b58decode(raw)

    if len(key_bytes) not in (32, 64):
        raise ValueError("Private key must decode to 32 or 64 bytes.")

    return key_bytes


def keypair_from_private_key(raw: str) -> Keypair:
    key_bytes = normalize_private_key(raw)
    if len(key_bytes) == 64:
        return Keypair.from_bytes(key_bytes)
    return Keypair.from_seed(key_bytes)


def import_wallet(raw_private_key: str) -> Tuple[str, str]:
    keypair = keypair_from_private_key(raw_private_key)
    public_key = str(keypair.pubkey())
    encrypted_private_key = encrypt_text(raw_private_key.strip())
    return public_key, encrypted_private_key


def create_wallet() -> Tuple[str, str]:
    keypair = Keypair()
    secret = base58.b58encode(bytes(keypair)).decode("utf-8")
    public_key = str(keypair.pubkey())
    encrypted_private_key = encrypt_text(secret)
    return public_key, encrypted_private_key


def decrypt_wallet_key(encrypted_private_key: str) -> Keypair:
    raw = decrypt_text(encrypted_private_key)
    return keypair_from_private_key(raw)


def is_valid_solana_address(address: str) -> bool:
    try:
        Pubkey.from_string(address.strip())
        return True
    except Exception:
        return False


def get_sol_balance(public_key: str, rpc_url: str) -> float:
    client = Client(rpc_url)
    result = client.get_balance(Pubkey.from_string(public_key))
    lamports = result.value or 0
    return lamports / 1_000_000_000
