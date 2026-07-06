# Trading System Upgrade

Upload these files to your GitHub repo root:

- `trading_engine.py`
- `positions_storage.py`
- `dm_trading.py`

Then update `bot.py` using:

- `telegram_trading_patch_example.py`

Also merge these into your existing files:

- `requirements-trading.txt` into `requirements.txt`
- `env-trading.example` into `.env.example`

## What this adds

- Buy flow in DM
- User sends CA
- Bot asks wallet percentage: 10%, 20%, 30%, 50%, 75%, 100%
- Custom SOL buy
- Jupiter swap integration
- Saves open positions
- Positions page
- Sell 25%, 50%, 100%
- Save TP/SL targets

## Important

This version saves TP/SL settings but does not yet auto-execute TP/SL.
The next upgrade will add a background monitor that checks prices and sells automatically.
