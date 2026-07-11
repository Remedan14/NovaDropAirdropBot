"""
Telegram bot for NovaDrop AirdqkqYU"
import logging
from typing import Optional

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)

from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from config import (
    BOT_TOKEN,
    CHANNELS,
    REFERRAL_REWARD,
    MIN_WITHDRAW,
    ADMIN_ID,
    CHANNEL_URLS
)

from database import (
    add_user,
    get_balance,
    add_referral_reward,
    save_wallet,
    create_withdrawal,
    get_user
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Keyboard layouts
MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["💰 Balance", "👥 Referrals"],
        ["📋 Tasks", "👛 Wallet"],
        ["💸 Withdraw"]
    ],
    resize_keyboard=True
)

WALLET_MENU = ReplyKeyboardMarkup(
    [
        ["USDT (TRC20)"],
        ["Bitcoin"],
        ["🔙 Back"]
    ],
    resize_keyboard=True
)


# ============================================================================
# Utility Functions
# ============================================================================

async def check_join(bot, user_id: int) -> bool:
    """
    Check whether the user joined all required channels.
    
    Args:
        bot: Telegram bot instance
        user_id: User ID to check
        
    Returns:
        True if user joined all channels, False otherwise
    """
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)
            
            if member.status in ["left", "kicked"]:
                logger.info(f"User {user_id} hasn't joined channel {channel}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking channel {channel} for user {user_id}: {e}")
            return False
    
    return True


def validate_usdt_trc20(address: str) -> bool:
    """Validate USDT TRC20 address format"""
    return address.startswith("T") and len(address) == 34


def validate_bitcoin(address: str) -> bool:
    """Basic Bitcoin address validation"""
    # Bitcoin addresses start with 1, 3, or bc1 and are 26-35 chars
    valid_starts = ["1", "3", "bc1"]
    return (any(address.startswith(start) for start in valid_starts) 
            and 26 <= len(address) <= 35)


# ============================================================================
# Core Handlers
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command
    """
    user = update.effective_user
    referred_by = None
    
    # Extract referral code
    if context.args:
        try:
            referred_by = int(context.args[0])
            logger.info(f"User {user.id} started with referral code {referred_by}")
        except (ValueError, IndexError) as e:
            logger.warning(f"Invalid referral code from user {user.id}: {e}")
            referred_by = None
    
    # Add user to database
    try:
        add_user(
            user.id,
            user.username or "unknown",
            user.first_name,
            referred_by
        )
        logger.info(f"User {user.id} added to database")
    except Exception as e:
        logger.error(f"Failed to add user {user.id} to database: {e}")
        await update.message.reply_text(
            "❌ Failed to initialize. Please try again later."
        )
        return
    
    # Store referrer in context for later use
    if referred_by:
        context.user_data["referrer"] = referred_by
    
    # Check if user joined channels
    joined = await check_join(context.bot, user.id)
    
    if not joined:
        # Build keyboard with channel links
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Channel 1", url=CHANNEL_URLS["channel_1"])],
            [InlineKeyboardButton("📢 Channel 2", url=CHANNEL_URLS["channel_2"])],
            [InlineKeyboardButton("✅ Verify", callback_data="verify")]
        ])
        
        await update.message.reply_text(
            "🔗 Join both Telegram channels first, then click Verify.",
            reply_markup=keyboard
        )
        return
    
    # User already verified
    context.user_data["verified"] = True
    await update.message.reply_text(
        f"👋 Welcome {user.first_name}!\n\n"
        f"💵 Earn ${REFERRAL_REWARD:.2f} for every valid referral.\n\n"
        f"Use the menu below to get started.",
        reply_markup=MAIN_MENU
    )


async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle verify button callback
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    
    # Check if user joined channels
    joined = await check_join(context.bot, user_id)
    
    if not joined:
        await query.message.reply_text(
            "❌ You haven't joined all required channels yet.\n"
            "Please join both channels and try again."
        )
        return
    
    # Check if already verified
    if context.user_data.get("verified"):
        await query.message.reply_text("✅ You are already verified!")
        return
    
    # Mark as verified
    context.user_data["verified"] = True
    logger.info(f"User {user_id} verified")
    
    # Process referral reward if applicable
    referrer_id = context.user_data.get("referrer")
    if referrer_id:
        try:
            add_referral_reward(referrer_id, REFERRAL_REWARD)
            logger.info(f"Referral reward ${REFERRAL_REWARD} added to user {referrer_id}")
        except Exception as e:
            logger.error(f"Failed to add referral reward: {e}")
    
    await query.message.reply_text(
        "✅ Verification successful!\n\n"
        "🎉 Welcome to NovaDrop Airdrop!\n\n"
        "Use the menu below to manage your account.",
        reply_markup=MAIN_MENU
    )


# ============================================================================
# User Actions
# ============================================================================

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show user balance
    """
    user_id = update.effective_user.id
    
    try:
        amount = get_balance(user_id)
        await update.message.reply_text(
            f"💰 Your Balance\n\n"
            f"USD: ${amount:.2f}",
            reply_markup=MAIN_MENU
        )
    except Exception as e:
        logger.error(f"Failed to get balance for user {user_id}: {e}")
        await update.message.reply_text(
            "❌ Failed to fetch balance. Try again later.",
            reply_markup=MAIN_MENU
        )


async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show referral link
    """
    user_id = update.effective_user.id
    
    try:
        bot = await context.bot.get_me()
        referral_link = f"https://t.me/{bot.username}?start={user_id}"
        
        await update.message.reply_text(
            f"👥 Your Referral Link\n\n"
            f"<code>{referral_link}</code>\n\n"
            f"💵 Reward: ${REFERRAL_REWARD:.2f} per valid referral",
            parse_mode="HTML",
            reply_markup=MAIN_MENU
        )
    except Exception as e:
        logger.error(f"Failed to generate referral link for user {user_id}: {e}")
        await update.message.reply_text(
            "❌ Failed to generate referral link. Try again later.",
            reply_markup=MAIN_MENU
        )


async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show wallet selection menu
    """
    context.user_data["wallet_menu"] = True
    
    await update.message.reply_text(
        "💳 Select wallet type to add your address:",
        reply_markup=WALLET_MENU
    )


async def usdt_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /usdt command to set USDT wallet
    """
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /usdt <wallet_address>\n\n"
            "Example: /usdt TN3W4H6rK...",
            reply_markup=MAIN_MENU
        )
        return
    
    wallet_address = context.args[0]
    
    # Validate address format
    if not validate_usdt_trc20(wallet_address):
        await update.message.reply_text(
            "❌ Invalid USDT TRC20 address.\n"
            "Address must start with 'T' and be 34 characters long.",
            reply_markup=MAIN_MENU
        )
        return
    
    try:
        save_wallet(user_id, "USDT_TRC20", wallet_address)
        logger.info(f"USDT wallet saved for user {user_id}")
        
        await update.message.reply_text(
            f"✅ USDT TRC20 wallet saved:\n\n"
            f"<code>{wallet_address}</code>",
            parse_mode="HTML",
            reply_markup=MAIN_MENU
        )
    except Exception as e:
        logger.error(f"Failed to save USDT wallet for user {user_id}: {e}")
        await update.message.reply_text(
            "❌ Failed to save wallet. Try again later.",
            reply_markup=MAIN_MENU
        )


async def bitcoin_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /btc command to set Bitcoin wallet
    """
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /btc <wallet_address>\n\n"
            "Example: /btc 1A1z...",
            reply_markup=MAIN_MENU
        )
        return
    
    wallet_address = context.args[0]
    
    # Validate address format
    if not validate_bitcoin(wallet_address):
        await update.message.reply_text(
            "❌ Invalid Bitcoin address.\n"
            "Address must start with 1, 3, or bc1.",
            reply_markup=MAIN_MENU
        )
        return
    
    try:
        save_wallet(user_id, "BITCOIN", wallet_address)
        logger.info(f"Bitcoin wallet saved for user {user_id}")
        
        await update.message.reply_text(
            f"✅ Bitcoin wallet saved:\n\n"
            f"<code>{wallet_address}</code>",
            parse_mode="HTML",
            reply_markup=MAIN_MENU
        )
    except Exception as e:
        logger.error(f"Failed to save Bitcoin wallet for user {user_id}: {e}")
        await update.message.reply_text(
            "❌ Failed to save wallet. Try again later.",
            reply_markup=MAIN_MENU
        )


async def handle_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /withdraw command to initiate withdrawal
    """
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /withdraw <amount>\n\n"
            "Example: /withdraw 10",
            reply_markup=MAIN_MENU
        )
        return
    
    # Validate and convert amount
    try:
        amount = float(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount. Please enter a valid number.",
            reply_markup=MAIN_MENU
        )
        return
    
    # Check minimum withdrawal
    if amount < MIN_WITHDRAW:
        await update.message.reply_text(
            f"❌ Minimum withdrawal is ${MIN_WITHDRAW:.2f}",
            reply_markup=MAIN_MENU
        )
        return
    
    # Check user balance
    try:
        balance = get_balance(user_id)
    except Exception as e:
        logger.error(f"Failed to get balance for user {user_id}: {e}")
        await update.message.reply_text(
            "❌ Failed to check balance. Try again later.",
            reply_markup=MAIN_MENU
        )
        return
    
    if balance < amount:
        await update.message.reply_text(
            f"❌ Insufficient balance.\n"
            f"Your balance: ${balance:.2f}\n"
            f"Requested: ${amount:.2f}",
            reply_markup=MAIN_MENU
        )
        return
    
    # Create withdrawal request
    try:
        withdrawal_id = create_withdrawal(user_id, amount)
        logger.info(f"Withdrawal #{withdrawal_id} created for user {user_id}: ${amount}")
        
        await update.message.reply_text(
            f"✅ Withdrawal request submitted!\n\n"
            f"ID: #{withdrawal_id}\n"
            f"Amount: ${amount:.2f}\n\n"
            f"⏳ Admin will review shortly.",
            reply_markup=MAIN_MENU
        )
        
        # Notify admin
        try:
            user_info = get_user(user_id)
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"🔔 New Withdrawal Request\n\n"
                    f"ID: #{withdrawal_id}\n"
                    f"User ID: {user_id}\n"
                    f"Username: @{user_info.get('username', 'unknown')}\n"
                    f"Amount: ${amount:.2f}\n"
                    f"Status: Pending"
                )
            )
        except Exception as e:
            logger.error(f"Failed to notify admin of withdrawal: {e}")
    
    except Exception as e:
        logger.error(f"Failed to create withdrawal for user {user_id}: {e}")
        await update.message.reply_text(
            "❌ Failed to process withdrawal. Try again later.",
            reply_markup=MAIN_MENU
        )


# ============================================================================
# Text Message Handlers
# ============================================================================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle text messages from the main menu
    """
    user_text = update.message.text
    
    if user_text == "💰 Balance":
        await balance(update, context)
    elif user_text == "👥 Referrals":
        await referral(update, context)
    elif user_text == "👛 Wallet":
        await wallet(update, context)
    elif user_text == "💸 Withdraw":
        await update.message.reply_text(
            "💸 Withdrawal\n\n"
            "Use the command below to withdraw:\n\n"
            "<code>/withdraw 10</code>",
            parse_mode="HTML",
            reply_markup=MAIN_MENU
        )
    elif user_text == "🔙 Back":
        await update.message.reply_text(
            "Back to main menu.",
            reply_markup=MAIN_MENU
        )
    else:
        await update.message.reply_text(
            "Please use the menu buttons.",
            reply_markup=MAIN_MENU
        )


# ============================================================================
# Register Handlers
# ============================================================================

def register_handlers(app) -> None:
    """
    Register all handlers to the application
    """
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("referral", referral))
    app.add_handler(CommandHandler("wallet", wallet))
    app.add_handler(CommandHandler("usdt", usdt_wallet))
    app.add_handler(CommandHandler("btc", bitcoin_wallet))
    app.add_handler(CommandHandler("withdraw", handle_withdraw))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    
    # Text message handler (must be last)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info("All handlers registered successfully")
