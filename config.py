
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"))

BOT_TOKEN = os.getenv("BOT_TOKEN")

WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    "https://nextgenincome10-cyber.github.io/NEXA-BOT/webapp/"
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "nexa.db"
)

APP_NAME = "NEXA"
CURRENCY = "USD"

MINIMUM_WITHDRAWAL = 1.0
MINING_ENABLED = True