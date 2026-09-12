import os

# ==============================
# NEXA BOT CONFIGURATION
# ==============================

# এখানে নিজের নতুন BotFather Token বসাও
BOT_TOKEN = "8897017525:AAEDWSyvqVEQSggWXkLwPeRlUKi3ty4L-To"


# ==============================
# NEXA MINI APP
# ==============================

WEBAPP_URL = (
    "https://YOUR-USERNAME.github.io/NEXA-BOT/webapp/"
)


# ==============================
# DATABASE
# ==============================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "nexa.db"
)


# ==============================
# APP INFORMATION
# ==============================

APP_NAME = "NEXA"
CURRENCY = "USD"


# ==============================
# MINING SETTINGS
# ==============================

MINING_ENABLED = True


# ==============================
# WITHDRAW SETTINGS
# ==============================

MINIMUM_WITHDRAWAL = 1.0


# ==============================
# DEBUG
# ==============================

DEBUG = False