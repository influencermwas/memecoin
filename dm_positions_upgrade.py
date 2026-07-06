from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram import Update

from positions_storage import get_positions


def positions_keyboard(positions) -> InlineKeyboardMarkup:
    rows = []
    for p in positions:
        mint = p["mint"]
        symbol = p.get("symbol") or "Token"
        rows.append([
            InlineKeyboardButton(f"Sell 25% {symbol}", callback_data=f"sell_pct:{mint}:25"),
            InlineKeyboardButton("Sell 50%", callback_data=f"sell_pct:{mint}:50"),
        ])
        rows.append([
            InlineKeyboardButton("Sell 100%", callback_data=f"sell_pct:{mint}:100"),
            InlineKeyboardButton("Set TP/SL", callback_data=f"set_risk_menu:{mint}"),
        ])
    rows.append([InlineKeyboardButton("← Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)


async def show_positions_live(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    rows = [p for p in get_positions(query.from_user.id) if p.get("status") == "open"]

    if not rows:
        await query.edit_message_text(
            "📈 *Positions*\n\nNo open positions yet.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🟢 Buy", callback_data="trade_buy")]])
        )
        return

    text = "📈 *Your Open Positions*\n\n"
    for p in rows:
        pnl = p.get("last_pnl_pct")
        pnl_text = f"{pnl}%" if pnl is not None else "Waiting for monitor"

        price = p.get("last_price_usd")
        price_text = f"${price}" if price else "Loading"

        text += (
            f"*{p.get('symbol') or 'Unknown'}*\n"
            f"CA: `{p['mint']}`\n"
            f"Entry SOL: *{p.get('entry_sol', '?')} SOL*\n"
            f"Entry Price: *${p.get('entry_price_usd', 'Setting soon')}*\n"
            f"Now: *{price_text}*\n"
            f"PnL: *{pnl_text}*\n"
            f"TP: *{p.get('take_profit_pct') or 'Not set'}%*\n"
            f"SL: *-{p.get('stop_loss_pct') or 'Not set'}%*\n\n"
        )

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=positions_keyboard(rows))
