import sqlite3
from config import DATABASE_NAME

conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
cursor = conn.cursor()

# Users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    balance REAL DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    referred_by INTEGER,
    usdt_wallet TEXT,
    btc_wallet TEXT,
    joined INTEGER DEFAULT 0
)
""")

# Withdrawal requests
cursor.execute("""
CREATE TABLE IF NOT EXISTS withdrawals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    wallet_type TEXT,
    wallet_address TEXT,
    amount REAL,
    status TEXT DEFAULT 'Pending'
)
""")

conn.commit()


def add_user(user_id, username, first_name, referred_by=None):
    cursor.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (user_id,)
    )

    if cursor.fetchone() is None:
        cursor.execute("""
        INSERT INTO users
        (user_id, username, first_name, referred_by)
        VALUES (?,?,?,?)
        """,
        (user_id, username, first_name, referred_by))
        conn.commit()


def get_balance(user_id):
    cursor.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,)
    )
    row = cursor.fetchone()

    if row:
        return row[0]

    return 0


def add_referral_reward(user_id, reward):
    cursor.execute("""
    UPDATE users
    SET balance = balance + ?,
        referrals = referrals + 1
    WHERE user_id=?
    """, (reward, user_id))
    conn.commit()


def save_wallet(user_id, wallet_type, wallet):
    if wallet_type == "USDT":
        cursor.execute(
            "UPDATE users SET usdt_wallet=? WHERE user_id=?",
            (wallet, user_id)
        )
    else:
        cursor.execute(
            "UPDATE users SET btc_wallet=? WHERE user_id=?",
            (wallet, user_id)
        )

    conn.commit()
