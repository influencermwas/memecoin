import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from wallet_manager import decrypt_wallet_key, is_valid_solana_address
from wallet_storage import get_active_wallet
from trading_engine import (
    buy_token_with_sol,
    sell_token_for_sol,
    percent_of_wallet_sol,
    get_token_balance_raw,
)
from positions_storage import save_position, get_positions, set_risk_orders, close_position

WAITING_BUY_CA = 2001
WAITING_CUSTOM_BUY_SOL = 2002
WAITING_TP_SL = 2003


def buy_percent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("10%", callback_data="buy_pct:10"),
         InlineKeyboardButton("20%", callback_data="buy_pct:20"),
         InlineKeyboardButton("30%", callback_data="buy_pct:30")],
        [InlineKeyboardButton("50%", callback_data="buy_pct:50"),
         InlineKeyboardButton("75%", callback_data="buy_pct:75"),
         InlineKeyboardButton("100%", callback_data="buy_pct:100")],
        [InlineKeyboardButton("Custom SOL", callback_data="buy_custom_sol")],
        [InlineKeyboardButton("Cancel", callback_data="main_menu")],
    ])


def after_buy_keyboard(mint: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("TP +50%", callback_data=f"risk:{mint}:50:none"),
         InlineKeyboardButton("TP 2X", callback_data=f"risk:{mint}:100:none")],
        [InlineKeyboardButton("SL -20%", callback_data=f"risk:{mint}:none:20"),
         InlineKeyboardButton("SL -30%", callback_data=f"risk:{mint}:none:30")],
        [InlineKeyboardButton("Set TP 2X + SL -20%", callback_data=f"risk:{mint}:100:20")],
        [InlineKeyboardButton("📈 Positions", callback_data="positions")],
    ])


def positions_keyboard(positions) -> InlineKeyboardMarkup:
    rows = []
    for p in positions:
        mint = p["mint"]
        rows.append([
            InlineKeyboardButton(f"Sell 25% {p.get('symbol', '')}", callback_data=f"sell_pct:{mint}:25"),
            InlineKeyboardButton("Sell 50%", callback_data=f"sell_pct:{mint}:50"),
        ])
        rows.append([
            InlineKeyboardButton("Sell 100%", callback_data=f"sell_pct:{mint}:100"),
            InlineKeyboardButton("Set TP/SL", callback_data=f"set_risk_menu:{mint}"),
        ])
    rows.append([InlineKeyboardButton("← Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)


async def buy_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    wallet = get_active_wallet(query.from_user.id)
    if not wallet:
        await query.edit_message_text("❌ No wallet found. Import or create wallet first.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Wallet", callback_data="wallet_menu")]
        ]))
        return ConversationHandler.END

    await query.edit_message_text(
        "🟢 *Buy Token*\n\n"
        "Send the meme coin contract address / CA.",
        parse_mode="Markdown",
    )
    return WAITING_BUY_CA


async def receive_buy_ca(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ca = update.message.text.strip()

    if not is_valid_solana_address(ca):
        await update.message.reply_text("❌ Invalid Solana CA. Send a valid token mint address.")
        return WAITING_BUY_CA

    context.user_data["buy_ca"] = ca

    await update.message.reply_text(
        "✅ CA received.\n\n"
        "Choose how much of your SOL wallet to use:",
        reply_markup=buy_percent_keyboard(),
    )
    return ConversationHandler.END


async def buy_percent_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    percent = float(query.data.split(":")[1])

    ca = context.user_data.get("buy_ca")
    wallet = get_active_wallet(user_id)

    if not ca:
        await query.edit_message_text("❌ No CA saved. Tap Buy again.")
        return
    if not wallet:
        await query.edit_message_text("❌ No active wallet.")
        return

    try:
        sol_amount = percent_of_wallet_sol(wallet["public_key"], percent)
        if sol_amount <= 0:
            await query.edit_message_text("❌ Not enough SOL. Fund wallet first.")
            return

        await query.edit_message_text(
            f"⏳ Buying `{ca}` using *{percent:.0f}%* of wallet = *{sol_amount} SOL*...\n\n"
            "Please wait.",
            parse_mode="Markdown",
        )

        keypair = decrypt_wallet_key(wallet["encrypted_private_key"])
        result = buy_token_with_sol(
            keypair=keypair,
            token_mint=ca,
            sol_amount=sol_amount,
            slippage_bps=int(context.user_data.get("slippage_bps", os.getenv("DEFAULT_SLIPPAGE_BPS", "500"))),
        )

        save_position(user_id, {
            "mint": ca,
            "wallet_label": wallet["label"],
            "wallet_public_key": wallet["public_key"],
            "entry_sol": sol_amount,
            "buy_signature": result["signature"],
            "raw_tokens": result.get("raw_out_amount"),
            "price_impact_pct": result.get("price_impact_pct"),
            "take_profit_pct": None,
            "stop_loss_pct": None,
        })

        await query.edit_message_text(
            "✅ *Buy Successful*\n\n"
            f"CA:\n`{ca}`\n\n"
            f"Spent: *{sol_amount} SOL*\n"
            f"Tx: `{result['signature']}`\n\n"
            "Now set TP/SL:",
            parse_mode="Markdown",
            reply_markup=after_buy_keyboard(ca),
        )

    except Exception as exc:
        await query.edit_message_text(f"❌ Buy failed:\n{exc}")


async def custom_buy_sol_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Send custom SOL amount to buy, example: `0.05`", parse_mode="Markdown")
    return WAITING_CUSTOM_BUY_SOL


async def custom_buy_sol_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    ca = context.user_data.get("buy_ca")
    wallet = get_active_wallet(user_id)

    try:
        sol_amount = float(update.message.text.strip())
        if sol_amount <= 0:
            raise ValueError("Amount must be above 0.")

        if not ca or not wallet:
            await update.message.reply_text("❌ Missing CA or wallet. Tap Buy again.")
            return ConversationHandler.END

        msg = await update.message.reply_text(f"⏳ Buying with {sol_amount} SOL...")
        keypair = decrypt_wallet_key(wallet["encrypted_private_key"])

        result = buy_token_with_sol(
            keypair=keypair,
            token_mint=ca,
            sol_amount=sol_amount,
            slippage_bps=int(context.user_data.get("slippage_bps", os.getenv("DEFAULT_SLIPPAGE_BPS", "500"))),
        )

        save_position(user_id, {
            "mint": ca,
            "wallet_label": wallet["label"],
            "wallet_public_key": wallet["public_key"],
            "entry_sol": sol_amount,
            "buy_signature": result["signature"],
            "raw_tokens": result.get("raw_out_amount"),
            "price_impact_pct": result.get("price_impact_pct"),
            "take_profit_pct": None,
            "stop_loss_pct": None,
        })

        await msg.edit_text(
            "✅ *Buy Successful*\n\n"
            f"CA:\n`{ca}`\n\n"
            f"Spent: *{sol_amount} SOL*\n"
            f"Tx: `{result['signature']}`",
            parse_mode="Markdown",
            reply_markup=after_buy_keyboard(ca),
        )
    except Exception as exc:
        await update.message.reply_text(f"❌ Buy failed: {exc}")

    return ConversationHandler.END


async def show_positions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        text += (
            f"Token: `{p['mint']}`\n"
            f"Wallet: *{p.get('wallet_label', 'W?')}*\n"
            f"Entry: *{p.get('entry_sol', '?')} SOL*\n"
            f"TP: *{p.get('take_profit_pct') or 'Not set'}%*\n"
            f"SL: *-{p.get('stop_loss_pct') or 'Not set'}%*\n\n"
        )

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=positions_keyboard(rows))


async def sell_percent_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    _, mint, pct = query.data.split(":")
    pct = float(pct)

    wallet = get_active_wallet(user_id)
    if not wallet:
        await query.edit_message_text("❌ No active wallet.")
        return

    try:
        raw_balance = get_token_balance_raw(wallet["public_key"], mint)
        sell_amount = int(raw_balance * pct / 100)

        if sell_amount <= 0:
            await query.edit_message_text("❌ No token balance to sell.")
            return

        await query.edit_message_text(f"⏳ Selling {pct:.0f}% of `{mint}`...", parse_mode="Markdown")

        keypair = decrypt_wallet_key(wallet["encrypted_private_key"])
        result = sell_token_for_sol(
            keypair=keypair,
            token_mint=mint,
            token_amount_raw=sell_amount,
            slippage_bps=int(context.user_data.get("slippage_bps", os.getenv("DEFAULT_SLIPPAGE_BPS", "500"))),
        )

        if pct >= 99:
            close_position(user_id, mint, {"sell_signature": result["signature"]})

        await query.edit_message_text(
            "✅ *Sell Successful*\n\n"
            f"Sold: *{pct:.0f}%*\n"
            f"Token: `{mint}`\n"
            f"Estimated SOL out: *{result.get('sol_out_estimate')} SOL*\n"
            f"Tx: `{result['signature']}`",
            parse_mode="Markdown",
        )
    except Exception as exc:
        await query.edit_message_text(f"❌ Sell failed:\n{exc}")


async def risk_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, mint, tp, sl = query.data.split(":")

    from positions_storage import get_positions, update_position

    current = None
    for p in get_positions(query.from_user.id):
        if p.get("mint") == mint and p.get("status") == "open":
            current = p
            break

    old_tp = current.get("take_profit_pct") if current else None
    old_sl = current.get("stop_loss_pct") if current else None

    tp_value = old_tp if tp == "none" else float(tp)
    sl_value = old_sl if sl == "none" else float(sl)

    update_position(query.from_user.id, mint, {
        "take_profit_pct": tp_value,
        "stop_loss_pct": sl_value,
    })

    await query.edit_message_text(
        "✅ *TP/SL saved*\n\n"
        f"Token: `{mint}`\n"
        f"TP: *{tp_value if tp_value is not None else 'Not set'}%*\n"
        f"SL: *-{sl_value if sl_value is not None else 'Not set'}%*\n\n"
        "Both TP and SL can now stay active together.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📈 Positions", callback_data="positions")]])
    )
