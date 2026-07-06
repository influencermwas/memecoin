import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from wallet_manager import create_wallet, import_wallet, get_sol_balance
from wallet_storage import (
    add_wallet,
    list_wallets,
    get_active_wallet,
    next_wallet_label,
    set_active_wallet,
    delete_wallet,
)

WAITING_IMPORT_KEY = 1001
WAITING_DELETE_LABEL = 1002


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Wallet", callback_data="wallet_menu"),
         InlineKeyboardButton("🟢 Buy", callback_data="trade_buy")],
        [InlineKeyboardButton("🔴 Sell", callback_data="trade_sell"),
         InlineKeyboardButton("📈 Positions", callback_data="positions")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
         InlineKeyboardButton("🔄 Refresh", callback_data="wallet_refresh")],
    ])


def wallet_keyboard(user_id: int) -> InlineKeyboardMarkup:
    wallets = list_wallets(user_id)
    rows = []

    wallet_buttons = []
    active = get_active_wallet(user_id)
    active_label = active["label"] if active else None

    for wallet in wallets:
        label = wallet["label"]
        title = f"✅ {label}" if label == active_label else label
        wallet_buttons.append(InlineKeyboardButton(title, callback_data=f"wallet_switch:{label}"))

    for i in range(0, len(wallet_buttons), 3):
        rows.append(wallet_buttons[i:i + 3])

    rows.extend([
        [InlineKeyboardButton("➕ Create Solana Wallet", callback_data="wallet_create")],
        [InlineKeyboardButton("📥 Import Phantom Wallet", callback_data="wallet_import")],
        [InlineKeyboardButton("🗑 Remove Wallet", callback_data="wallet_delete_start")],
        [InlineKeyboardButton("🔄 Refresh Balance", callback_data="wallet_refresh")],
        [InlineKeyboardButton("← Back", callback_data="main_menu")],
    ])
    return InlineKeyboardMarkup(rows)


async def start_dm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🚀 *INFLUENCER MEMECOIN BOT*\n\n"
        "Channel signals continue running.\n"
        "In DM you can manage wallet, buy, sell and view positions.\n\n"
        "Start with *Wallet*."
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard())


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = "🏠 *Main Menu*\n\nChoose an action."
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard())


async def show_wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id if query else update.effective_user.id
    active = get_active_wallet(user_id)
    rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

    if active:
        try:
            balance = get_sol_balance(active["public_key"], rpc_url)
            balance_text = f"{balance:.6f} SOL"
        except Exception:
            balance_text = "Could not refresh"
        text = (
            "💰 *Solana Wallets*\n\n"
            f"Active: *{active['label']}*\n"
            f"`{active['public_key']}`\n"
            f"Balance: *{balance_text}*\n\n"
            "Select wallet or import/create new one."
        )
    else:
        text = (
            "💰 *Solana Wallets*\n\n"
            "No wallet connected yet.\n\n"
            "Create a new wallet or import your Phantom wallet."
        )

    if query:
        await query.answer()
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=wallet_keyboard(user_id))
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=wallet_keyboard(user_id))


async def create_wallet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    label = next_wallet_label(user_id)
    public_key, encrypted_key = create_wallet()
    add_wallet(user_id, label, public_key, encrypted_key)

    await query.edit_message_text(
        "✅ *Wallet Created*\n\n"
        f"Label: *{label}*\n"
        f"Address:\n`{public_key}`\n\n"
        "Fund this wallet with SOL before buying.",
        parse_mode="Markdown",
        reply_markup=wallet_keyboard(user_id),
    )


async def import_wallet_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📥 *Import Phantom Wallet*\n\n"
        "Send your Phantom private key now.\n\n"
        "Accepted formats:\n"
        "• Base58 private key\n"
        "• JSON array private key\n\n"
        "⚠️ For safety, use a fresh trading wallet. Do not import your main savings wallet.\n\n"
        "[Cancel with /cancel]",
        parse_mode="Markdown",
    )
    return WAITING_IMPORT_KEY


async def import_wallet_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    raw_key = update.message.text.strip()

    try:
        label = next_wallet_label(user_id)
        public_key, encrypted_key = import_wallet(raw_key)
        add_wallet(user_id, label, public_key, encrypted_key)

        try:
            await update.message.delete()
        except Exception:
            pass

        await update.effective_chat.send_message(
            "✅ *Wallet Imported Successfully*\n\n"
            f"Label: *{label}*\n"
            f"Address:\n`{public_key}`\n\n"
            "Your private key was encrypted before saving.",
            parse_mode="Markdown",
            reply_markup=wallet_keyboard(user_id),
        )
    except Exception as exc:
        await update.message.reply_text(
            f"❌ Import failed: {exc}\n\nSend a valid Phantom private key or /cancel.",
        )
        return WAITING_IMPORT_KEY

    return ConversationHandler.END


async def switch_wallet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    label = query.data.split(":", 1)[1]

    if set_active_wallet(user_id, label):
        await show_wallet_menu(update, context)
    else:
        await query.edit_message_text("❌ Wallet not found.", reply_markup=wallet_keyboard(user_id))


async def delete_wallet_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    wallets = list_wallets(query.from_user.id)
    if not wallets:
        await query.edit_message_text("No wallet to remove.", reply_markup=wallet_keyboard(query.from_user.id))
        return ConversationHandler.END

    rows = [[InlineKeyboardButton(w["label"], callback_data=f"wallet_delete:{w['label']}")] for w in wallets]
    rows.append([InlineKeyboardButton("← Back", callback_data="wallet_menu")])
    await query.edit_message_text(
        "🗑 Choose wallet to remove from this bot.\n\n"
        "This does not delete the blockchain wallet.",
        reply_markup=InlineKeyboardMarkup(rows),
    )
    return ConversationHandler.END


async def delete_wallet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    label = query.data.split(":", 1)[1]
    delete_wallet(user_id, label)
    await query.edit_message_text(f"✅ Removed {label}.", reply_markup=wallet_keyboard(user_id))


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Cancelled.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END
