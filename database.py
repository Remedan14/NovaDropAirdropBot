import sqlite3

db = sqlite3.connect(
    "users.db",
    check_same_thread=False
)

cursor = db.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
username TEXT,
balance REAL DEFAULT 0,
referrer INTEGER,
usdt_wallet TEXT,
btc_wallet TEXT
)
""")

db.commit()


def add_user(user_id, username, referrer=None):

    cursor.execute(
        "SELECT id FROM users WHERE id=?",
        (user_id,)
    )

    if not cursor.fetchone():

        cursor.execute(
        """
        INSERT INTO users
        (id,username,referrer)
        VALUES(?,?,?)
        """,
        (user_id,username,referrer)
        )

        db.commit()


def get_balance(user_id):

    cursor.execute(
        "SELECT balance FROM users WHERE id=?",
        (user_id,)
    )

    return cursor.fetchone()[0]


def add_balance(user_id, amount):

    cursor.execute(
        """
        UPDATE users
        SET balance=balance+?
        WHERE id=?
        """,
        (amount,user_id)
    )

    db.commit()
