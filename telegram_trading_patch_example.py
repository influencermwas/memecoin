"""
Copy these imports and handlers into your existing bot.py after adding wallet system.

This file is an example patch only. Do not run it directly.
"""

from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from dm_trading import (
    WAITING_BUY_CA,
    WAITING_CUSTOM_BUY_SOL,
    buy_start,
    receive_buy_ca,
    buy_percent_callback,
    custom_buy_sol_start,
    custom_buy_sol_receive,
    show_positions,
    sell_percent_callback,
    risk_callback,
)

# Add this after Application object is created:
#
# app = Application.builder().token(BOT_TOKEN).build()

buy_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(buy_start, pattern="^trade_buy$")],
    states={
        WAITING_BUY_CA: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_buy_ca)
        ],
    },
    fallbacks=[],
)

custom_buy_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(custom_buy_sol_start, pattern="^buy_custom_sol$")],
    states={
        WAITING_CUSTOM_BUY_SOL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, custom_buy_sol_receive)
        ],
    },
    fallbacks=[],
)

app.add_handler(buy_conversation)
app.add_handler(custom_buy_conversation)
app.add_handler(CallbackQueryHandler(buy_percent_callback, pattern="^buy_pct:"))
app.add_handler(CallbackQueryHandler(show_positions, pattern="^positions$"))
app.add_handler(CallbackQueryHandler(sell_percent_callback, pattern="^sell_pct:"))
app.add_handler(CallbackQueryHandler(risk_callback, pattern="^risk:"))
