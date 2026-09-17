
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from config import DATABASE_PATH


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    database_directory = os.path.dirname(DATABASE_PATH)

    if database_directory:
        os.makedirs(database_directory, exist_ok=True)

    connection = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():
    connection = get_connection()

    schema_path = os.path.join(
        os.path.dirname(__file__),
        "database",
        "schema.sql"
    )

    with open(schema_path, "r", encoding="utf-8") as file:
        schema = file.read()

    connection.executescript(schema)
    connection.commit()
    connection.close()

    print("Database initialized successfully.")


# =========================================================
# USER FUNCTIONS
# =========================================================

def get_or_create_user(
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )

    user = cursor.fetchone()

    if user:
        cursor.execute(
            """
            UPDATE users
            SET username = ?,
                first_name = ?,
                last_name = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ?
            """,
            (
                username,
                first_name,
                last_name,
                telegram_id
            )
        )

        connection.commit()

        cursor.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )

        user = cursor.fetchone()
        connection.close()

        return dict(user)

    referral_code = f"NEXA{telegram_id}"

    cursor.execute(
        """
        INSERT INTO users (
            telegram_id,
            username,
            first_name,
            last_name,
            referral_code
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            telegram_id,
            username,
            first_name,
            last_name,
            referral_code
        )
    )

    user_id = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO balances (
            user_id,
            balance_usd,
            total_earned_usd,
            total_withdrawn_usd
        )
        VALUES (?, 0, 0, 0)
        """,
        (user_id,)
    )

    connection.commit()

    cursor.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    )

    user = cursor.fetchone()
    connection.close()

    return dict(user)


def get_user_by_telegram_id(telegram_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )

    user = cursor.fetchone()
    connection.close()

    if user:
        return dict(user)

    return None


# =========================================================
# BALANCE FUNCTIONS
# =========================================================

def get_balance(telegram_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT balances.*
        FROM balances
        INNER JOIN users
            ON users.id = balances.user_id
        WHERE users.telegram_id = ?
        """,
        (telegram_id,)
    )

    balance = cursor.fetchone()
    connection.close()

    if balance:
        return dict(balance)

    return None


def update_balance(
    telegram_id: int,
    amount: float,
    update_total_earned: bool = True
):
    connection = get_connection()
    cursor = connection.cursor()

    if update_total_earned:
        cursor.execute(
            """
            UPDATE balances
            SET balance_usd = balance_usd + ?,
                total_earned_usd = total_earned_usd + ?
            WHERE user_id = (
                SELECT id
                FROM users
                WHERE telegram_id = ?
            )
            """,
            (
                amount,
                amount,
                telegram_id
            )
        )
    else:
        cursor.execute(
            """
            UPDATE balances
            SET balance_usd = balance_usd + ?
            WHERE user_id = (
                SELECT id
                FROM users
                WHERE telegram_id = ?
            )
            """,
            (
                amount,
                telegram_id
            )
        )

    connection.commit()
    connection.close()


def update_withdrawn_balance(
    telegram_id: int,
    amount: float
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE balances
        SET balance_usd = balance_usd - ?,
            total_withdrawn_usd = total_withdrawn_usd + ?
        WHERE user_id = (
            SELECT id
            FROM users
            WHERE telegram_id = ?
        )
        """,
        (
            amount,
            amount,
            telegram_id
        )
    )

    connection.commit()
    connection.close()


# =========================================================
# NETWORK FUNCTIONS
# =========================================================

def get_active_networks():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM networks
        WHERE active = 1
        ORDER BY id ASC
        """
    )

    networks = cursor.fetchall()
    connection.close()

    return [dict(network) for network in networks]


def get_network(network_code: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM networks
        WHERE code = ?
        """,
        (network_code,)
    )

    network = cursor.fetchone()
    connection.close()

    if network:
        return dict(network)

    return None


def update_network_address(
    network_code: str,
    address: str
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE networks
        SET address = ?
        WHERE code = ?
    """, (
        address,
        network_code
    ))

    connection.commit()

    updated = cursor.rowcount > 0

    connection.close()

    return updated


def add_network(
    name: str,
    code: str,
    address: Optional[str] = None
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO networks (
            name,
            code,
            address,
            active
        )
        VALUES (?, ?, ?, 1)
        """,
        (
            name,
            code,
            address
        )
    )

    connection.commit()
    network_id = cursor.lastrowid
    connection.close()

    return network_id


def set_network_status(
    network_code: str,
    active: bool
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE networks
        SET active = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE code = ?
        """,
        (
            1 if active else 0,
            network_code
        )
    )

    connection.commit()
    connection.close()


# =========================================================
# FEE / TAX FUNCTIONS
# =========================================================

def get_active_fees(applies_to: Optional[str] = None):
    connection = get_connection()
    cursor = connection.cursor()

    if applies_to:
        cursor.execute(
            """
            SELECT *
            FROM fees
            WHERE active = 1
              AND applies_to = ?
            ORDER BY id ASC
            """,
            (applies_to,)
        )
    else:
        cursor.execute(
            """
            SELECT *
            FROM fees
            WHERE active = 1
            ORDER BY id ASC
            """
        )

    fees = cursor.fetchall()
    connection.close()

    return [dict(fee) for fee in fees]


def add_fee(
    name: str,
    description: str,
    fee_type: str,
    fee_value: float,
    applies_to: str
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO fees (
            name,
            description,
            fee_type,
            fee_value,
            applies_to,
            active
        )
        VALUES (?, ?, ?, ?, ?, 1)
        """,
        (
            name,
            description,
            fee_type,
            fee_value,
            applies_to
        )
    )

    connection.commit()
    fee_id = cursor.lastrowid
    connection.close()

    return fee_id


def update_fee(
    fee_id: int,
    name: str,
    description: str,
    fee_type: str,
    fee_value: float,
    applies_to: str,
    active: bool
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE fees
        SET name = ?,
            description = ?,
            fee_type = ?,
            fee_value = ?,
            applies_to = ?,
            active = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            name,
            description,
            fee_type,
            fee_value,
            applies_to,
            1 if active else 0,
            fee_id
        )
    )

    connection.commit()
    updated = cursor.rowcount > 0
    connection.close()

    return updated


def set_fee_status(
    fee_id: int,
    active: bool
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE fees
        SET active = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            1 if active else 0,
            fee_id
        )
    )

    connection.commit()
    connection.close()


# =========================================================
# ADMIN SETTINGS
# =========================================================

def get_setting(
    setting_key: str,
    default=None
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT setting_value
        FROM admin_settings
        WHERE setting_key = ?
        """,
        (setting_key,)
    )

    row = cursor.fetchone()
    connection.close()

    if row:
        return row["setting_value"]

    return default


def set_setting(
    setting_key: str,
    setting_value: str
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO admin_settings (
            setting_key,
            setting_value
        )
        VALUES (?, ?)
        ON CONFLICT(setting_key)
        DO UPDATE SET
            setting_value = excluded.setting_value,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            setting_key,
            setting_value
        )
    )

    connection.commit()
    connection.close()


# =========================================================
# TRANSACTIONS
# =========================================================

def add_transaction(
    telegram_id: int,
    transaction_type: str,
    amount_usd: float,
    description: str = "",
    reference_id: Optional[int] = None
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO transactions (
            user_id,
            type,
            amount_usd,
            description,
            reference_id
        )
        SELECT id, ?, ?, ?, ?
        FROM users
        WHERE telegram_id = ?
        """,
        (
            transaction_type,
            amount_usd,
            description,
            reference_id,
            telegram_id
        )
    )

    connection.commit()
    transaction_id = cursor.lastrowid
    connection.close()

    return transaction_id


def get_user_transactions(
    telegram_id: int,
    limit: int = 50
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT transactions.*
        FROM transactions
        INNER JOIN users
            ON users.id = transactions.user_id
        WHERE users.telegram_id = ?
        ORDER BY transactions.id DESC
        LIMIT ?
        """,
        (
            telegram_id,
            limit
        )
    )

    transactions = cursor.fetchall()
    connection.close()

    return [dict(item) for item in transactions]


# =========================================================
# TASKS
# =========================================================

def get_active_tasks():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM tasks
        WHERE active = 1
        ORDER BY id ASC
        """
    )

    tasks = cursor.fetchall()
    connection.close()

    return [dict(task) for task in tasks]


def add_task(
    title: str,
    description: str,
    reward_usd: float,
    task_type: str,
    target: str
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO tasks (
            title,
            description,
            reward_usd,
            task_type,
            target,
            active
        )
        VALUES (?, ?, ?, ?, ?, 1)
        """,
        (
            title,
            description,
            reward_usd,
            task_type,
            target
        )
    )

    connection.commit()
    task_id = cursor.lastrowid
    connection.close()

    return task_id


def set_task_status(
    task_id: int,
    active: bool
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET active = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            1 if active else 0,
            task_id
        )
    )

    connection.commit()
    connection.close()


# =========================================================
# NOTIFICATIONS
# =========================================================

def add_notification(
    user_id: Optional[int],
    title: str,
    message: str
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO notifications (
            user_id,
            title,
            message
        )
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            title,
            message
        )
    )

    connection.commit()
    notification_id = cursor.lastrowid
    connection.close()

    return notification_id


def get_user_notifications(
    telegram_id: int,
    limit: int = 50
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT notifications.*
        FROM notifications
        INNER JOIN users
            ON users.id = notifications.user_id
        WHERE users.telegram_id = ?
        ORDER BY notifications.id DESC
        LIMIT ?
        """,
        (
            telegram_id,
            limit
        )
    )

    notifications = cursor.fetchall()
    connection.close()

    return [dict(item) for item in notifications]


# =========================================================
# REFERRALS
# =========================================================

def get_referral_count(
    telegram_id: int
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM referrals
        WHERE referrer_id = (
            SELECT id
            FROM users
            WHERE telegram_id = ?
        )
        """,
        (telegram_id,)
    )

    result = cursor.fetchone()
    connection.close()

    return result["total"] if result else 0


# =========================================================
# WITHDRAWAL / DEPOSIT HELPERS
# =========================================================

def create_withdrawal(
    telegram_id: int,
    amount_usd: float,
    network_code: str,
    wallet_address: str
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO withdrawals (
            user_id,
            amount_usd,
            network_code,
            wallet_address,
            status
        )
        SELECT id, ?, ?, ?, 'pending'
        FROM users
        WHERE telegram_id = ?
        """,
        (
            amount_usd,
            network_code,
            wallet_address,
            telegram_id
        )
    )

    connection.commit()
    withdrawal_id = cursor.lastrowid
    connection.close()

    return withdrawal_id


def create_deposit(
    telegram_id: int,
    amount_usd: float,
    network_code: str,
    wallet_address: Optional[str] = None,
    transaction_hash: Optional[str] = None
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO deposits (
            user_id,
            amount_usd,
            network_code,
            wallet_address,
            transaction_hash,
            status
        )
        SELECT id, ?, ?, ?, ?, 'pending'
        FROM users
        WHERE telegram_id = ?
        """,
        (
            amount_usd,
            network_code,
            wallet_address,
            transaction_hash,
            telegram_id
        )
    )

    connection.commit()
    deposit_id = cursor.lastrowid
    connection.close()

    return deposit_id


# =========================================================
# MINING FUNCTIONS
# =========================================================

def get_active_user_miner(user_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT user_miners.*, miners.daily_rate_usd,
               miners.duration_days, miners.name
        FROM user_miners
        INNER JOIN miners
            ON miners.id = user_miners.miner_id
        WHERE user_miners.user_id = ?
          AND user_miners.active = 1
          AND miners.active = 1
        LIMIT 1
        """,
        (user_id,)
    )

    miner = cursor.fetchone()
    connection.close()

    if miner:
        return dict(miner)

    return None


def start_mining_session(user_miner_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM mining_sessions
        WHERE user_miner_id = ?
        """,
        (user_miner_id,)
    )

    existing = cursor.fetchone()

    if existing:
        connection.close()
        return existing["id"]

    cursor.execute(
        """
        INSERT INTO mining_sessions
            (user_miner_id, earned_usd)
        VALUES (?, 0)
        """,
        (user_miner_id,)
    )

    connection.commit()
    session_id = cursor.lastrowid
    connection.close()

    return session_id


# =========================================================
# MINING EARNING CALCULATION
# =========================================================

def calculate_mining_earning(session_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            mining_sessions.*,
            user_miners.user_id,
            miners.daily_rate_usd,
            miners.duration_days
        FROM mining_sessions
        INNER JOIN user_miners
            ON user_miners.id = mining_sessions.user_miner_id
        INNER JOIN miners
            ON miners.id = user_miners.miner_id
        WHERE mining_sessions.id = ?
          AND user_miners.active = 1
          AND miners.active = 1
        """,
        (session_id,)
    )

    session = cursor.fetchone()

    if not session:
        connection.close()
        return None

    session = dict(session)

    now = datetime.now(timezone.utc)

    last_calculated_value = session.get("last_calculated_at")

    if not last_calculated_value:
        connection.close()
        return 0.0

    last_calculated_text = str(last_calculated_value).replace(
        " ",
        "T"
    )

    try:
        last_calculated = datetime.fromisoformat(
            last_calculated_text
        )
    except ValueError:
        connection.close()
        return 0.0

    if last_calculated.tzinfo is None:
        last_calculated = last_calculated.replace(
            tzinfo=timezone.utc
        )
    else:
        last_calculated = last_calculated.astimezone(
            timezone.utc
        )

    elapsed_seconds = (
        now - last_calculated
    ).total_seconds()

    if elapsed_seconds <= 0:
        connection.close()
        return 0.0

    earned = (
        elapsed_seconds / 86400
    ) * session["daily_rate_usd"]

    connection.close()

    return round(earned, 8)


# =========================================================
# ACTIVE MINERS
# =========================================================

def get_active_miners():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, name, description, price_usd,
               daily_rate_usd, duration_days
        FROM miners
        WHERE active = 1
        ORDER BY price_usd ASC
        """
    )

    miners = [dict(row) for row in cursor.fetchall()]
    connection.close()

    return miners
    # =========================================================
# ADMIN FUNCTIONS
# =========================================================

def get_all_users(limit=50):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            users.*,
            COALESCE(balances.balance_usd, 0) AS balance_usd
        FROM users
        LEFT JOIN balances
            ON users.id = balances.user_id
        ORDER BY users.id DESC
        LIMIT ?
    """, (limit,))

    users = [dict(row) for row in cursor.fetchall()]
    connection.close()

    return users


def get_admin_statistics():
    connection = get_connection()
    cursor = connection.cursor()

    stats = {}

    cursor.execute("SELECT COUNT(*) AS total FROM users")
    stats["users"] = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COALESCE(SUM(balance_usd), 0) AS total
        FROM balances
    """)
    stats["balance"] = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM withdrawals
        WHERE status = 'pending'
    """)
    stats["pending_withdrawals"] = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM deposits
        WHERE status = 'pending'
    """)
    stats["pending_deposits"] = cursor.fetchone()["total"]

    connection.close()

    return stats


def get_all_tasks():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM tasks
        ORDER BY id DESC
    """)

    tasks = [dict(row) for row in cursor.fetchall()]
    connection.close()

    return tasks


def get_all_networks():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM networks
        ORDER BY id ASC
    """)

    networks = [dict(row) for row in cursor.fetchall()]
    connection.close()

    return networks