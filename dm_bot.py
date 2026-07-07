import os
from dotenv import load_dotenv
from telegram import BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, filters

from dm_wallet import *
from dm_trading import *
from dm_positions_upgrade import show_positions_live
from jobs import setup_jobs
from dm_tpsl_menu import set_risk_menu
from dm_protect_profit import protect_profit_menu, protect_profit_set
from dm_settings import settings_menu, slippage_set
from dm_withdraw import WAITING_WITHDRAW_ADDRESS, WAITING_WITHDRAW_AMOUNT, withdraw_start, withdraw_receive_address, withdraw_receive_amount

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")

async def post_init(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Open main menu"),
        BotCommand("wallet", "Open wallet menu"),
        BotCommand("buy", "Buy token"),
        BotCommand("positions", "View positions"),
        BotCommand("cancel", "Cancel current action"),
    ])

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN or TELEGRAM_BOT_TOKEN missing in .env")

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    setup_jobs(app)

    app.add_handler(CommandHandler("start", start_dm))
    app.add_handler(CommandHandler("wallet", show_wallet_menu))
    app.add_handler(CommandHandler("buy", buy_start))
    app.add_handler(CommandHandler("positions", show_positions_live))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(import_wallet_start, pattern="^wallet_import$")],
        states={WAITING_IMPORT_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, import_wallet_receive)]},
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(buy_start, pattern="^trade_buy$")],
        states={WAITING_BUY_CA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_buy_ca)]},
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    ))


    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(withdraw_start, pattern="^withdraw_sol$")],
        states={
            WAITING_WITHDRAW_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_receive_address)],
            WAITING_WITHDRAW_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_receive_amount)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(custom_buy_sol_start, pattern="^buy_custom_sol$")],
        states={WAITING_CUSTOM_BUY_SOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_buy_sol_receive)]},
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    ))

    app.add_handler(CallbackQueryHandler(show_main_menu, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(show_wallet_menu, pattern="^wallet_menu$"))
    app.add_handler(CallbackQueryHandler(create_wallet_callback, pattern="^wallet_create$"))
    app.add_handler(CallbackQueryHandler(switch_wallet_callback, pattern="^wallet_switch:"))
    app.add_handler(CallbackQueryHandler(delete_wallet_start, pattern="^wallet_delete_start$"))
    app.add_handler(CallbackQueryHandler(delete_wallet_callback, pattern="^wallet_delete:"))
    app.add_handler(CallbackQueryHandler(show_wallet_menu, pattern="^wallet_refresh$"))

    app.add_handler(CallbackQueryHandler(buy_percent_callback, pattern="^buy_pct:"))
    app.add_handler(CallbackQueryHandler(settings_menu, pattern="^settings$"))
    app.add_handler(CallbackQueryHandler(slippage_set, pattern="^slippage_set:"))
    app.add_handler(CallbackQueryHandler(show_positions_live, pattern="^positions$"))
    app.add_handler(CallbackQueryHandler(sell_percent_callback, pattern="^sell_pct:"))
    app.add_handler(CallbackQueryHandler(protect_profit_menu, pattern="^pp:"))
    app.add_handler(CallbackQueryHandler(protect_profit_set, pattern="^pps:"))
    app.add_handler(CallbackQueryHandler(set_risk_menu, pattern="^set_risk_menu:"))
    app.add_handler(CallbackQueryHandler(risk_callback, pattern="^risk:"))

    print("DM trading bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
