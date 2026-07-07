from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

def settings_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Slippage 1%", callback_data="slippage_set:100"),
         InlineKeyboardButton("Slippage 3%", callback_data="slippage_set:300")],
        [InlineKeyboardButton("Slippage 5%", callback_data="slippage_set:500"),
         InlineKeyboardButton("Slippage 10%", callback_data="slippage_set:1000")],
        [InlineKeyboardButton("← Back", callback_data="main_menu")]
    ])

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    current = context.user_data.get("slippage_bps", "default")

    await q.edit_message_text(
        "⚙️ *Settings*\n\n"
        f"Current slippage: *{current if current == 'default' else str(int(current)/100) + '%'}*\n\n"
        "Choose slippage:",
        parse_mode="Markdown",
        reply_markup=settings_keyboard()
    )

async def slippage_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    bps = int(q.data.split(":")[1])
    context.user_data["slippage_bps"] = bps

    await q.edit_message_text(
        f"✅ Slippage set to *{bps/100}%*",
        parse_mode="Markdown",
        reply_markup=settings_keyboard()
    )
