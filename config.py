import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load .env from the NEXA-BOT folder
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Telegram Bot Token
# Keep your token inside .env — never share it publicly.
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Telegram Mini App URL
WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    "https://nextgenincome10-cyber.github.io/NEXA-BOT/webapp/"
)

# Database
DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "nexa.db"
)

# App settings
APP_NAME = "NEXA"
CURRENCY = "USD"

# Withdrawal settings
MINIMUM_WITHDRAWAL = 1.0

# Mining
MINING_ENABLED = True