# Solana Memecoin Channel Bot

Automatic Telegram channel/group broadcaster for Solana memecoin signals.

## Features
- Solana token detection from DexScreener profiles
- Silent watchlist mode
- Must-pass safety rules
- RugCheck summary support
- Smart money placeholder/proxy
- Trend strength
- Entry zone
- Profit plan
- Token logo/photo signal posts
- Live updates: +50%, 2X, 3X, 5X, 10X, cut loss
- Daily recap

## Setup

1. Create a Telegram bot with @BotFather.
2. Add the bot as admin in your Telegram channel/group.
3. Copy `.env.example` to `.env` and fill:

```env
BOT_TOKEN=your_bot_token
CHANNEL_ID=@your_channel_username
```

4. Install and run:

```bash
pip install -r requirements.txt
python bot.py
```

## Notes

This is version 1. For real smart-money wallet tracking and dev-wallet history, connect a Solana transaction API such as Helius/Shyft/QuickNode and feed the wallet events into `smart_money.py` and a dev history database.

Memecoins are extremely risky. This bot is not financial advice.
