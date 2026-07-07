from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from positions_storage import update_position

def protect_keyboard(mint):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("+20%", callback_data=f"pps:{mint}:20"),
         InlineKeyboardButton("+30%", callback_data=f"pps:{mint}:30")],
        [InlineKeyboardButton("+50%", callback_data=f"pps:{mint}:50"),
         InlineKeyboardButton("+75%", callback_data=f"pps:{mint}:75")],
        [InlineKeyboardButton("Disable", callback_data=f"pps:{mint}:disable")],
        [InlineKeyboardButton("📈 Positions", callback_data="positions")]
    ])

async def protect_profit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    mint = q.data.split(":", 1)[1]

    await q.edit_message_text(
        "🛡 *Protect Profit*\n\n"
        f"Token:\n`{mint}`\n\n"
        "Choose profit level to protect.\n\n"
        "Example: if trade is +70% and you choose +30%, bot sells if profit drops back to +30%.",
        parse_mode="Markdown",
        reply_markup=protect_keyboard(mint)
    )

async def protect_profit_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, mint, value = q.data.split(":")

    if value == "disable":
        update_position(q.from_user.id, mint, {"profit_protect_pct": None})
        text = "✅ Profit protection disabled."
    else:
        pct = float(value)
        update_position(q.from_user.id, mint, {"profit_protect_pct": pct})
        text = (
            "✅ *Profit Protection Enabled*\n\n"
            f"Token:\n`{mint}`\n\n"
            f"Protected profit: *+{pct:.0f}%*\n\n"
            f"If profit falls to +{pct:.0f}%, bot will auto-sell."
        )

    await q.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📈 Positions", callback_data="positions")]])
    )
