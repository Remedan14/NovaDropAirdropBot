import os
from typing import List

# Load and validate required environment variables
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
if not ADMIN_ID:
    raise ValueError("ADMIN_ID environment variable is not set")

# Mandatory channels
CHANNELS: List[str] = [
    "@NovaDropAirdrop",
    "@NovaDropAirdrop2"
]

# Referral reward amount (USD per referral)
REFERRAL_REWARD: float = 0.50

# Minimum withdrawal amount (USD)
MIN_WITHDRAW: float = 5.00

# Supported wallets
SUPPORTED_WALLETS: List[str] = [
    "USDT (TRC20)",
    "Bitcoin"
]

# Database
DATABASE_NAME: str = "novadrop.db"
