import os
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken


def _derive_key(secret: str) -> bytes:
    """
    Derives a Fernet key from WALLET_MASTER_KEY.
    Use one long random value in .env, never commit it to GitHub.
    """
    if not secret or len(secret) < 32:
        raise ValueError("WALLET_MASTER_KEY must be at least 32 characters.")
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def get_fernet() -> Fernet:
    master_key = os.getenv("WALLET_MASTER_KEY", "")
    return Fernet(_derive_key(master_key))


def encrypt_text(value: str) -> str:
    return get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_text(token: str) -> str:
    try:
        return get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Could not decrypt wallet. Check WALLET_MASTER_KEY.") from exc
