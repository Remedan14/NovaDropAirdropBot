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
def save_wallet(user_id, usdt, btc):

    cursor.execute(
        """
        UPDATE users 
        SET usdt_wallet=?, btc_wallet=?
        WHERE id=?
        """,
        (usdt, btc, user_id)
    )

    db.commit()
def add_withdrawal(user_id, amount):

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS withdrawals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        status TEXT DEFAULT 'pending'
        )
        """
    )

    cursor.execute(
        """
        INSERT INTO withdrawals(user_id, amount)
        VALUES(?,?)
        """,
        (user_id, amount)
    )

    db.commit()



def get_pending_withdrawals():

    cursor.execute(
        """
        SELECT * FROM withdrawals
        WHERE status='pending'
        """
    )

    return cursor.fetchall()



def update_withdrawal(wid, status):

    cursor.execute(
        """
        UPDATE withdrawals
        SET status=?
        WHERE id=?
        """,
        (status,wid)
    )

    db.commit()

def get_all_users():

    cursor.execute("SELECT id FROM users")

    return cursor.fetchall()


def get_user_wallet(user_id):

    cursor.execute(
        """
        def check_referred(user_id):

    cursor.execute(
        "SELECT referrer FROM users WHERE id=?",
        (user_id,)
    )

    result = cursor.fetchone()

    if result:
        return result[0]

    return None



def set_referral_reward(user_id):

    cursor.execute(
        """
        UPDATE users
        SET referrer=NULL
        WHERE id=?
        """,
        (user_id,)
    )

    db.commit()
        SELECT usdt_wallet, btc_wallet 
        FROM users 
        WHERE id=?
        """,
        (user_id,)
        def add_balance(user_id, amount):

    cursor.execute(
        """
        UPDATE users
        SET balance = balance + ?
        WHERE id=?
        """,
        (amount, user_id)
    )

    db.commit()



def get_users():

    cursor.execute(
        "SELECT id, username, balance FROM users"
    )

    return cursor.fetchall()
