from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from config import (
    BOT_TOKEN,
    CHANNELS,
    REFERRAL_REWARD
)

from database import (
    add_user,
    get_balance,
    add_referral_reward
)


async def check_join(bot, user_id):
    """
    Check whether the user joined all required channels.
    """

    for channel in CHANNELS:

        try:

            member = await bot.get_chat_member(
                channel,
                user_id
            )

            if member.status in [
                "left",
                "kicked"
            ]:
                return False

        except:

            return False

    return True
    from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton
)

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["💰 Balance", "👥 Referrals"],
        ["📋 Tasks", "👛 Wallet"],
        ["💸 Withdraw"]
    ],
    resize_keyboard=True
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    referred_by = None

    if context.args:
        try:
            referred_by = int(context.args[0])
        except:
            referred_by = None

    add_user(
        user.id,
        user.username,
        user.first_name,
        referred_by
    )

    joined = await check_join(
        context.bot,
        user.id
    )

    if not joined:

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📢 Channel 1",
                        url="https://t.me/NovaDropAirdrop"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📢 Channel 2",
                        url="https://t.me/NovaDropAirdrop2"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "✅ Verify",
                        callback_data="verify"
                    )
                ]
            ]
        )

        await update.message.reply_text(
            "Join both Telegram channels first.",
            reply_markup=keyboard
        )

        return

    await update.message.reply_text(
        f"Welcome {user.first_name}!\n\n"
        f"Earn ${REFERRAL_REWARD:.2f} for every valid referral.",
        reply_markup=MAIN_MENU
        )
  async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = query.from_user

    joined = await check_join(
        context.bot,
        user.id
    )

    if not joined:

        await query.message.reply_text(
            "❌ You haven't joined all required channels."
        )

        return

    if context.user_data.get("verified"):

        await query.message.reply_text(
            "✅ You are already verified."
        )

        return

    context.user_data["verified"] = True

    if context.user_data.get("referrer"):

        add_referral_reward(
            context.user_data["referrer"],
            REFERRAL_REWARD
        )

    await query.message.reply_text(
        "✅ Verification successful!\n\n"
        "Welcome to NovaDrop Airdrop.",
        reply_markup=MAIN_MENU
        )
      app.add_handler(
    CallbackQueryHandler(
        verify,
        pattern="verify"
    )
    )
from telegram.ext import MessageHandler, filters


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    amount = get_balance(user_id)

    await update.message.reply_text(
        f"💰 Your Balance\n\n"
        f"USD: ${amount:.2f}"
    )


async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):

    bot = await context.bot.get_me()

    link = (
        f"https://t.me/{bot.username}"
        f"?start={update.effective_user.id}"
    )

    await update.message.reply_text(
        f"👥 Your Referral Link\n\n"
        f"{link}\n\n"
        f"Reward: ${REFERRAL_REWARD:.2f} "
        f"for every valid referral."
    )


async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = ReplyKeyboardMarkup(
        [
            ["USDT (TRC20)"],
            ["Bitcoin"],
            ["🔙 Back"]
        ],
        resize_keyboard=True
    )

    context.user_data["wallet_menu"] = True

    await update.message.reply_text(
        "Select wallet type.",
        reply_markup=keyboard
    )


async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):

    amount = get_balance(update.effective_user.id)

    if amount < MIN_WITHDRAW:

        await update.message.reply_text(
            f"❌ Minimum withdrawal is "
            f"${MIN_WITHDRAW:.2f}"
        )

        return

    await update.message.reply_text(
        "Enter your withdrawal amount."
    )

    context.user_data["withdraw"] = True
from config import BOT_TOKEN, ADMIN_ID
from database import (
    add_user,
    get_user,
    save_wallet,
    create_withdrawal
)
async def usdt_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text(
            "Fakkeenya:\n/usdt wallet_address"
        )
        return

    wallet = context.args[0]

    save_wallet(
        user_id,
        "USDT_TRC20",
        wallet
    )

    await update.message.reply_text(
        "✅ USDT TRC20 wallet keessan kuufameera."
    )


async def bitcoin_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text(
            "Fakkeenya:\n/btc wallet_address"
        )
        return

    wallet = context.args[0]

    save_wallet(
        user_id,
        "BITCOIN",
        wallet
    )

    await update.message.reply_text(
        "✅ Bitcoin wallet keessan kuufameera."
)

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text(
            "Fakkeenya:\n/withdraw 10"
        )
        return

    amount = context.args[0]

    create_withdrawal(
        user_id,
        amount
    )

    await update.message.reply_text(
        "✅ Withdrawal request keessan ergameera.\n"
        "Admin mirkaneessa."
    )


    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "🔔 New Withdrawal Request\n\n"
            f"User ID: {user_id}\n"
            f"Amount: {amount} USD"
        )
    )
app.add_handler(CommandHandler("usdt", usdt_wallet))
app.add_handler(CommandHandler("btc", bitcoin_wallet))
app.add_handler(CommandHandler("withdraw", withdraw))
