"""
Copy these imports and handlers into your existing bot.py.

This file is an example patch only. Do not run it directly.
"""

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from dm_wallet import (
    WAITING_IMPORT_KEY,
    start_dm,
    show_main_menu,
    show_wallet_menu,
    create_wallet_callback,
    import_wallet_start,
    import_wallet_receive,
    switch_wallet_callback,
    delete_wallet_start,
    delete_wallet_callback,
    cancel_conversation,
)

# After you create your Application object:
#
# app = Application.builder().token(BOT_TOKEN).build()
#
# Add these handlers:

wallet_import_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(import_wallet_start, pattern="^wallet_import$")],
    states={
        WAITING_IMPORT_KEY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, import_wallet_receive)
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_conversation)],
)

app.add_handler(CommandHandler("start", start_dm))
app.add_handler(wallet_import_conversation)
app.add_handler(CallbackQueryHandler(show_main_menu, pattern="^main_menu$"))
app.add_handler(CallbackQueryHandler(show_wallet_menu, pattern="^wallet_menu$"))
app.add_handler(CallbackQueryHandler(create_wallet_callback, pattern="^wallet_create$"))
app.add_handler(CallbackQueryHandler(switch_wallet_callback, pattern="^wallet_switch:"))
app.add_handler(CallbackQueryHandler(delete_wallet_start, pattern="^wallet_delete_start$"))
app.add_handler(CallbackQueryHandler(delete_wallet_callback, pattern="^wallet_delete:"))
app.add_handler(CallbackQueryHandler(show_wallet_menu, pattern="^wallet_refresh$"))

# Temporary placeholders until trading engine files are added:
# app.add_handler(CallbackQueryHandler(buy_start, pattern="^trade_buy$"))
# app.add_handler(CallbackQueryHandler(sell_start, pattern="^trade_sell$"))
# app.add_handler(CallbackQueryHandler(show_positions, pattern="^positions$"))
