from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from positions_storage import set_risk_orders

def tpsl_keyboard(mint: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("TP +50%", callback_data=f"risk:{mint}:50:none"),
         InlineKeyboardButton("TP 2X", callback_data=f"risk:{mint}:100:none")],
        [InlineKeyboardButton("TP 3X", callback_data=f"risk:{mint}:200:none"),
         InlineKeyboardButton("TP 5X", callback_data=f"risk:{mint}:400:none")],
        [InlineKeyboardButton("SL -10%", callback_data=f"risk:{mint}:none:-10"),
         InlineKeyboardButton("SL -20%", callback_data=f"risk:{mint}:none:-20")],
        [InlineKeyboardButton("Profit SL +20%", callback_data=f"risk:{mint}:none:20"),
         InlineKeyboardButton("Profit SL +30%", callback_data=f"risk:{mint}:none:30")],
        [InlineKeyboardButton("TP 2X + SL -20%", callback_data=f"risk:{mint}:100:20")],
        [InlineKeyboardButton("TP 3X + SL -30%", callback_data=f"risk:{mint}:200:30")],
        [InlineKeyboardButton("📈 Positions", callback_data="positions")],
    ])

async def set_risk_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    mint = q.data.split(":", 1)[1]

    await q.edit_message_text(
        "🛡 *Set TP / SL*\n\n"
        f"Token CA:\n`{mint}`\n\n"
        "Choose protection:",
        parse_mode="Markdown",
        reply_markup=tpsl_keyboard(mint)
    )
