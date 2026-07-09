
import telebot
from telebot import types

from config import *
from database import *


bot = telebot.TeleBot(TOKEN)



def joined(user_id):

    for ch in CHANNELS:

        try:
            status = bot.get_chat_member(
                ch,
                user_id
            ).status

            if status not in [
                "member",
                "administrator",
                "creator"
            ]:
                return False

        except:
            return False

    return True



@bot.message_handler(commands=['start'])
def start(message):

    user_id = message.from_user.id

    args = message.text.split()

    ref = None

    if len(args)>1:
        ref = args[1]


    add_user(
        user_id,
        message.from_user.username,
        ref
    )


    if not joined(user_id):

        kb=types.InlineKeyboardMarkup()

        for ch in CHANNELS:
            kb.add(
            types.InlineKeyboardButton(
            "Join "+ch,
            url="https://t.me/"+ch.replace("@","")
            ))

        kb.add(
        types.InlineKeyboardButton(
        "✅ Verify",
        callback_data="verify"
        ))

        bot.send_message(
        message.chat.id,
        "Join both channels first:",
        reply_markup=kb
        )

    else:
        menu(message)



@bot.callback_query_handler(
func=lambda c:c.data=="verify"
)
def verify(call):

    if joined(call.from_user.id):

        menu(call.message)

    else:
        bot.answer_callback_query(
        call.id,
        "You didn't join all channels"
        )



def menu(message):

    kb=types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.add(
    "💰 Balance",
    "👥 Referral"
    )

    kb.add(
    "💳 Wallet",
    "💸 Withdraw"
    )

    bot.send_message(
    message.chat.id,
    "Welcome NovaDrop 🚀",
    reply_markup=kb
    )



@bot.message_handler(
func=lambda m:m.text=="💰 Balance"
)
def balance(message):

    bal=get_balance(
    message.from_user.id
    )

    bot.send_message(
    message.chat.id,
    f"💰 Balance: ${bal}"
    )



@bot.message_handler(
func=lambda m:m.text=="👥 Referral"
)
def referral(message):

    link=f"https://t.me/{bot.get_me().username}?start={message.from_user.id}"

    bot.send_message(
    message.chat.id,
    f"""
Your referral link:

{link}

Reward:
$0.10 per valid referral
"""
)



@bot.message_handler(
func=lambda m:m.text=="💳 Wallet"
)
def wallet(message):

    bot.send_message(
    message.chat.id,
    """
Send wallet:

Format:

USDT:
BTC:
"""
)

    bot.register_next_step_handler(
        message,
        save_wallet
    )



def save_wallet(message):

    text=message.text

    bot.send_message(
    message.chat.id,
    "✅ Wallet saved"
    )



@bot.message_handler(
func=lambda m:m.text=="💸 Withdraw"
)
def withdraw(message):

    bot.send_message(
    message.chat.id,
    "Send withdrawal amount:"
    )



print("NovaDrop Bot Started")

bot.infinity_polling()
@bot.message_handler(func=lambda m:m.text=="💳 Wallet")
def wallet(message):

    bot.send_message(
        message.chat.id,
        """
Wallet galchi:

Fakkeenya:

USDT: Txxxxxxxxxx
BTC: bc1xxxxxxxx
"""
    )

    bot.register_next_step_handler(
        message,
        save_wallet_data
    )


def save_wallet_data(message):

    lines = message.text.split("\n")

    usdt = ""
    btc = ""

    for line in lines:
        if "USDT" in line:
            usdt = line.replace("USDT:","").strip()

        if "BTC" in line:
            btc = line.replace("BTC:","").strip()


    save_wallet(
        message.from_user.id,
        usdt,
        btc
    )

    bot.send_message(
        message.chat.id,
        "✅ Wallet saved successfully"
        )
    @bot.message_handler(commands=['broadcast'])
def broadcast(message):

    if message.from_user.id != ADMIN_ID:
        return

    msg = message.text.replace(
        "/broadcast ",
        ""
    )

    users = get_all_users()

    for user in users:
        try:
            bot.send_message(
                user[0],
                msg
            )
            @bot.message_handler(commands=['admin'])
def admin_panel(message):

    if message.from_user.id != ADMIN_ID:
        return

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "📢 Broadcast",
            callback_data="broadcast"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "💸 Pending Withdrawals",
            callback_data="withdrawals"
        )
    )

    bot.send_message(
        message.chat.id,
        "👑 Admin Panel",
        reply_markup=kb
    )



@bot.callback_query_handler(
func=lambda c:c.data=="withdrawals"
)
def pending_withdrawals(call):

    if call.from_user.id != ADMIN_ID:
        return

    withdrawals = get_pending_withdrawals()

    if not withdrawals:
        bot.send_message(
            call.message.chat.id,
            "No pending withdrawals"
        )
        return


    for w in withdrawals:

        kb = types.InlineKeyboardMarkup()

        kb.add(
            types.InlineKeyboardButton(
                "✅ Approve",
                callback_data=f"approve_{w[0]}"
            ),
            types.InlineKeyboardButton(
                "❌ Reject",
                callback_data=f"reject_{w[0]}"
            )
        )


        bot.send_message(
            call.message.chat.id,
            f"""
💸 Withdrawal

ID: {w[0]}
User: {w[1]}
Amount: ${w[2]}
Status: {w[3]}
""",
            reply_markup=kb
        )



@bot.callback_query_handler(
func=lambda c:c.data.startswith("approve_") or c.data.startswith("reject_")
)
def withdrawal_action(call):

    if call.from_user.id != ADMIN_ID:
        return


    data = call.data.split("_")

    action = data[0]
    wid = data[1]


    if action=="approve":

        update_withdrawal(
            wid,
            "approved"
        )

        bot.send_message(
            call.message.chat.id,
            "✅ Withdrawal approved"
        )


    elif action=="reject":

        update_withdrawal(
            wid,
            "rejected"
        )

        bot.send_message(
            call.message.chat.id,
            "❌ Withdrawal rejected"
            referrer = check_referred(call.from_user.id)

if referrer:

    add_balance(
        referrer,
        0.10
    )

    set_referral_reward(
        call.from_user.id
        )
        )
        except:
            pass


    bot.send_message(
        message.chat.id,
        "✅ Broadcast sent"
)
