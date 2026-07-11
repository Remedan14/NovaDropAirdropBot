import sqlite3
import logging
from config import DATABASE_NAME

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """Database manager for SQLite operations with error handling and thread safety."""
    
    def __init__(self, db_name=DATABASE_NAME):
        """Initialize database connection and create tables."""
        try:
            self.conn = sqlite3.connect(db_name, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            self.cursor = self.conn.cursor()
            self._init_tables()
            logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def _init_tables(self):
        """Create tables if they don't exist."""
        try:
            # Users table
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                first_name TEXT NOT NULL,
                balance REAL DEFAULT 0 CHECK(balance >= 0),
                referrals INTEGER DEFAULT 0 CHECK(referrals >= 0),
                referred_by INTEGER,
                usdt_wallet TEXT,
                btc_wallet TEXT,
                joined INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referred_by) REFERENCES users(user_id)
            )
            """)
            
            # Withdrawal requests table
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                wallet_type TEXT NOT NULL CHECK(wallet_type IN ('USDT', 'BTC')),
                wallet_address TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Approved', 'Rejected', 'Completed')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """)
            
            self.conn.commit()
            logger.info("Tables created/verified successfully")
        except sqlite3.Error as e:
            logger.error(f"Table creation error: {e}")
            raise
    
    def add_user(self, user_id, username, first_name, referred_by=None):
        """Add a new user to the database."""
        if not username or not first_name:
            logger.warning("Username and first_name cannot be empty")
            return False
        
        try:
            self.cursor.execute("""
            INSERT INTO users
            (user_id, username, first_name, referred_by)
            VALUES (?, ?, ?, ?)
            """, (user_id, username, first_name, referred_by))
            self.conn.commit()
            logger.info(f"User {user_id} ({username}) added successfully")
            return True
        except sqlite3.IntegrityError as e:
            logger.warning(f"User {user_id} already exists or duplicate username: {e}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def get_user(self, user_id):
        """Get user information by user_id."""
        try:
            self.cursor.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None
    
    def get_balance(self, user_id):
        """Get user's current balance."""
        try:
            self.cursor.execute(
                "SELECT balance FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = self.cursor.fetchone()
            return row[0] if row else 0
        except sqlite3.Error as e:
            logger.error(f"Error fetching balance for user {user_id}: {e}")
            return 0
    
    def add_referral_reward(self, user_id, reward):
        """Add referral reward to user's balance."""
        if reward < 0:
            logger.warning(f"Invalid reward amount: {reward}")
            return False
        
        try:
            self.cursor.execute("""
            UPDATE users
            SET balance = balance + ?,
                referrals = referrals + 1
            WHERE user_id = ?
            """, (reward, user_id))
            self.conn.commit()
            logger.info(f"Referral reward {reward} added to user {user_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding referral reward: {e}")
            return False
    
    def save_wallet(self, user_id, wallet_type, wallet_address):
        """Save wallet address for user."""
        if wallet_type not in ["USDT", "BTC"]:
            logger.warning(f"Invalid wallet type: {wallet_type}")
            return False
        
        if not wallet_address or len(wallet_address.strip()) == 0:
            logger.warning("Wallet address cannot be empty")
            return False
        
        try:
            if wallet_type == "USDT":
                self.cursor.execute(
                    "UPDATE users SET usdt_wallet = ? WHERE user_id = ?",
                    (wallet_address, user_id)
                )
            elif wallet_type == "BTC":
                self.cursor.execute(
                    "UPDATE users SET btc_wallet = ? WHERE user_id = ?",
                    (wallet_address, user_id)
                )
            
            self.conn.commit()
            logger.info(f"{wallet_type} wallet saved for user {user_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving wallet: {e}")
            return False
    
    def get_wallet(self, user_id, wallet_type):
        """Get wallet address for user."""
        if wallet_type not in ["USDT", "BTC"]:
            logger.warning(f"Invalid wallet type: {wallet_type}")
            return None
        
        try:
            column = "usdt_wallet" if wallet_type == "USDT" else "btc_wallet"
            self.cursor.execute(
                f"SELECT {column} FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = self.cursor.fetchone()
            return row[0] if row else None
        except sqlite3.Error as e:
            logger.error(f"Error fetching wallet: {e}")
            return None
    
    def create_withdrawal(self, user_id, wallet_type, amount):
        """Create a withdrawal request."""
        if wallet_type not in ["USDT", "BTC"]:
            logger.warning(f"Invalid wallet type: {wallet_type}")
            return False
        
        if amount <= 0:
            logger.warning(f"Invalid withdrawal amount: {amount}")
            return False
        
        try:
            # Check if user has sufficient balance
            balance = self.get_balance(user_id)
            if balance < amount:
                logger.warning(f"Insufficient balance for user {user_id}")
                return False
            
            # Get wallet address
            wallet = self.get_wallet(user_id, wallet_type)
            if not wallet:
                logger.warning(f"No {wallet_type} wallet saved for user {user_id}")
                return False
            
            # Create withdrawal request
            self.cursor.execute("""
            INSERT INTO withdrawals
            (user_id, wallet_type, wallet_address, amount)
            VALUES (?, ?, ?, ?)
            """, (user_id, wallet_type, wallet, amount))
            
            # Deduct from balance
            self.cursor.execute("""
            UPDATE users
            SET balance = balance - ?
            WHERE user_id = ?
            """, (amount, user_id))
            
            self.conn.commit()
            logger.info(f"Withdrawal request created for user {user_id}: {amount} {wallet_type}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error creating withdrawal: {e}")
            self.conn.rollback()
            return False
    
    def get_withdrawals(self, user_id, status=None):
        """Get withdrawal history for user."""
        try:
            if status:
                self.cursor.execute("""
                SELECT * FROM withdrawals
                WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC
                """, (user_id, status))
            else:
                self.cursor.execute("""
                SELECT * FROM withdrawals
                WHERE user_id = ?
                ORDER BY created_at DESC
                """, (user_id,))
            
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error fetching withdrawals: {e}")
            return []
    
    def update_withdrawal_status(self, withdrawal_id, status):
        """Update withdrawal request status."""
        if status not in ["Pending", "Approved", "Rejected", "Completed"]:
            logger.warning(f"Invalid status: {status}")
            return False
        
        try:
            self.cursor.execute("""
            UPDATE withdrawals
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """, (status, withdrawal_id))
            self.conn.commit()
            logger.info(f"Withdrawal {withdrawal_id} status updated to {status}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating withdrawal status: {e}")
            return False
    
    def close(self):
        """Close database connection."""
        try:
            self.conn.close()
            logger.info("Database connection closed")
        except sqlite3.Error as e:
            logger.error(f"Error closing database: {e}")


# Singleton instance
_db = None

def get_db():
    """Get or create database instance."""
    global _db
    if _db is None:
        _db = Database()
    return _db

def close_db():
    """Close database connection."""
    global _db
    if _db is not None:
        _db.close()
        _db = None
