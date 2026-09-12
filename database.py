import os
import sqlite3
from typing import Optional

from config import DATABASE_PATH


def get_connection():
    os.makedirs(
        os.path.dirname(DATABASE_PATH),
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def init_db():
    connection = get_connection()

    schema_path = os.path.join(
        os.path.dirname(__file__),
        "database",
        "schema.sql"
    )

    with open(
        schema_path,
        "r",
        encoding="utf-8"
    ) as file:
        schema = file.read()

    connection.executescript(schema)
    connection.commit()
    connection.close()

    print("Database initialized successfully.")


def get_or_create_user(
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None
):
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = ?
        """,
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
            """
            SELECT *
            FROM users
            WHERE telegram_id = ?
            """,
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
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    connection.close()

    return dict(user)


def get_user_by_telegram_id(
    telegram_id: int
):
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = ?
        """,
        (telegram_id,)
    )

    user = cursor.fetchone()

    connection.close()

    if user:
        return dict(user)

    return None


def get_balance(
    telegram_id: int
):
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            balances.*
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
    amount: float
):
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE balances
        SET balance_usd = balance_usd + ?,
            total_earned_usd =
                total_earned_usd + ?
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