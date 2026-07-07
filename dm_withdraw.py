from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solana.rpc.api import Client
import os

from wallet_storage import get_active_wallet
from wallet_manager import decrypt_wallet_key

WAITING_WITHDRAW_ADDRESS = 3001
WAITING_WITHDRAW_AMOUNT = 3002

LAMPORTS_PER_SOL = 1_000_000_000

def rpc():
    return Client(os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"))

def withdraw_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Cancel", callback_data="wallet_menu")]
    ])

async def withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    wallet = get_active_wallet(q.from_user.id)
    if not wallet:
        await q.edit_message_text("❌ No active wallet. Import/create wallet first.")
        return ConversationHandler.END

    context.user_data["withdraw_wallet"] = wallet

    await q.edit_message_text(
        "🏧 *Withdraw SOL*\n\n"
        f"From wallet: *{wallet['label']}*\n"
        f"`{wallet['public_key']}`\n\n"
        "Send destination Solana address:",
        parse_mode="Markdown",
        reply_markup=withdraw_keyboard()
    )
    return WAITING_WITHDRAW_ADDRESS

async def withdraw_receive_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    address = update.message.text.strip()

    try:
        Pubkey.from_string(address)
    except Exception:
        await update.message.reply_text("❌ Invalid Solana address. Send again.")
        return WAITING_WITHDRAW_ADDRESS

    context.user_data["withdraw_to"] = address

    await update.message.reply_text(
        "Enter amount of SOL to withdraw, example: `0.05`",
        parse_mode="Markdown"
    )
    return WAITING_WITHDRAW_AMOUNT

async def withdraw_receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    wallet = get_active_wallet(user_id)
    to_address = context.user_data.get("withdraw_to")

    try:
        amount = float(update.message.text.strip())
        if amount <= 0:
            raise ValueError("Amount must be above 0")
    except Exception:
        await update.message.reply_text("❌ Invalid amount. Example: 0.05")
        return WAITING_WITHDRAW_AMOUNT

    try:
        keypair = decrypt_wallet_key(wallet["encrypted_private_key"])
        client = rpc()

        balance = client.get_balance(Pubkey.from_string(wallet["public_key"])).value or 0
        lamports = int(amount * LAMPORTS_PER_SOL)

        fee_buffer = int(0.00001 * LAMPORTS_PER_SOL)
        if balance < lamports + fee_buffer:
            await update.message.reply_text("❌ Not enough SOL including network fee.")
            return ConversationHandler.END

        blockhash = client.get_latest_blockhash().value.blockhash

        ix = transfer(
            TransferParams(
                from_pubkey=keypair.pubkey(),
                to_pubkey=Pubkey.from_string(to_address),
                lamports=lamports
            )
        )

        msg = MessageV0.try_compile(
            payer=keypair.pubkey(),
            instructions=[ix],
            address_lookup_table_accounts=[],
            recent_blockhash=blockhash
        )

        tx = VersionedTransaction(msg, [keypair])
        result = client.send_raw_transaction(bytes(tx))
        sig = str(result.value)

        await update.message.reply_text(
            "✅ *Withdrawal Sent*\n\n"
            f"Amount: *{amount} SOL*\n"
            f"To:\n`{to_address}`\n\n"
            f"Tx:\n`{sig}`",
            parse_mode="Markdown"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Withdraw failed:\n`{e}`", parse_mode="Markdown")

    return ConversationHandler.END
