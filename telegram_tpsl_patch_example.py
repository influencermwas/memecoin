"""
Copy this into your existing bot.py after app creation.

Requires:
- price_monitor.py
- tp_sl_engine.py
- jobs.py
"""

from jobs import setup_jobs

# After:
# app = Application.builder().token(BOT_TOKEN).build()
#
# Add:
setup_jobs(app)

# Optional: replace old positions handler with live positions:
#
# from dm_positions_upgrade import show_positions_live
# app.add_handler(CallbackQueryHandler(show_positions_live, pattern="^positions$"))
#
# If you already have show_positions registered, remove the old one first.
