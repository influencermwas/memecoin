# Wallet System Upgrade

Upload these files to the root of your GitHub repository:

- `security.py`
- `wallet_storage.py`
- `wallet_manager.py`
- `dm_wallet.py`

Also update:

- `requirements.txt` with the packages in `requirements-wallet.txt`
- `.env.example` with the variables in `env-wallet.example`
- `bot.py` using the example in `telegram_wallet_patch_example.py`

## What this adds

- Telegram DM wallet menu
- Create Solana wallet
- Import Phantom/Solflare private key
- Encrypt private key before storage
- Multiple wallets: W1, W2, W3...
- Switch active wallet
- Refresh SOL balance
- Remove wallet from bot

## Important

Do not commit your real `.env` file.

For production, use a fresh trading wallet only, not a main savings wallet.
