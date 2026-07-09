import sqlite3

db = sqlite3.connect("novadrop.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance REAL DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    referred_by INTEGER,
    usdt_wallet TEXT,
    btc_wallet TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS withdrawals(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    wallet_type TEXT,
    wallet TEXT,
    amount REAL,
    status TEXT DEFAULT 'Pending'
)
""")

db.commit()
