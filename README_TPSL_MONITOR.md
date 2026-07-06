# Automatic TP/SL Monitor

Upload these files to your GitHub repo root:

- `price_monitor.py`
- `tp_sl_engine.py`
- `jobs.py`
- `dm_positions_upgrade.py`

Then patch `bot.py` using:

- `telegram_tpsl_patch_example.py`

Also merge:

- `requirements-tpsl.txt` into `requirements.txt`
- `env-tpsl.example` into `.env.example`

## What it does

- Checks all open positions every 60 seconds
- Gets live price from DexScreener
- Saves entry price on first monitor check if missing
- Updates position PnL
- Auto-sells when TP or SL is hit
- Sends DM notification after successful/failed auto-sell

## Important

For most accurate PnL, the next upgrade should save exact entry price immediately after buy.
This version starts TP/SL from the first DexScreener price found after buy.
