import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    WebAppInfo,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN, WEBAPP_URL

from database import (
    init_db,
    get_or_create_user,
    get_all_users,
    get_admin_statistics,
    get_all_tasks,
    get_all_networks,
    update_network_address,
    set_task_status,
    get_connection
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is missing. Add it to the .env file."
    )

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


class WalletAddressState(StatesGroup):
    waiting_for_address = State()


# =========================================================
# ADMIN SETTINGS
# =========================================================

ADMIN_TELEGRAM_ID = os.getenv(
    "ADMIN_TELEGRAM_ID",
    ""
).strip()


def is_admin(user_id: int) -> bool:
    return str(user_id) == ADMIN_TELEGRAM_ID


# =========================================================
# ADMIN KEYBOARD
# =========================================================

def admin_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="👥 Users",
                    callback_data="admin_users"
                ),
                InlineKeyboardButton(
                    text="📋 Tasks",
                    callback_data="admin_tasks"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💳 Deposit Wallets",
                    callback_data="admin_wallets"
                ),
                InlineKeyboardButton(
                    text="💸 Withdrawals",
                    callback_data="admin_withdrawals"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📊 Statistics",
                    callback_data="admin_statistics"
                ),
                InlineKeyboardButton(
                    text="🌐 Networks",
                    callback_data="admin_networks"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📢 Notifications",
                    callback_data="admin_notifications"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Close Panel",
                    callback_data="admin_close"
                )
            ]

        ]
    )


def back_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Back to Admin",
                    callback_data="admin_home"
                )
            ]
        ]
    )


# =========================================================
# START COMMAND
# =========================================================

@dp.message(CommandStart())
async def start_command(message: Message):

    user = message.from_user

    if not user:
        return

    get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="🚀 Open NEXA",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )

    keyboard.adjust(1)

    first_name = user.first_name or "User"

    await message.answer(
        f"👋 Welcome to NEXA, {first_name}!\n\n"
        "Manage your mining dashboard, balance, tasks, "
        "referrals and account activity from the NEXA Mini App.\n\n"
        "Tap the button below to open NEXA.",
        reply_markup=keyboard.as_markup()
    )


# =========================================================
# ADMIN COMMAND
# =========================================================

@dp.message(Command("admin"))
async def admin_command(message: Message):

    user = message.from_user

    if not user:
        return

    if not is_admin(user.id):

        await message.answer(
            "❌ You are not authorized to access the Admin Panel."
        )

        return

    await message.answer(
        "🔐 NEXA ADMIN PANEL\n\n"
        "Select an option below:",
        reply_markup=admin_keyboard()
    )


# =========================================================
# USERS
# =========================================================

async def show_users(callback: CallbackQuery):

    users = get_all_users(limit=20)

    if not users:

        text = "👥 USERS\n\nNo users found."

    else:

        text = "👥 USERS — Latest 20\n\n"

        for user in users:

            name = (
                user.get("first_name")
                or user.get("username")
                or "Unknown"
            )

            telegram_id = user.get("telegram_id")
            balance = user.get("balance_usd", 0)

            text += (
                f"👤 {name}\n"
                f"🆔 ID: {telegram_id}\n"
                f"💰 Balance: ${balance:.4f}\n"
                "──────────────\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard()
    )


# =========================================================
# STATISTICS
# =========================================================

async def show_statistics(callback: CallbackQuery):

    stats = get_admin_statistics()

    text = (
        "📊 NEXA STATISTICS\n\n"
        f"👥 Total Users: {stats.get('users', 0)}\n"
        f"💰 Total Balance: "
        f"${stats.get('balance', 0):.4f}\n"
        f"💸 Pending Withdrawals: "
        f"{stats.get('pending_withdrawals', 0)}\n"
        f"💳 Pending Deposits: "
        f"{stats.get('pending_deposits', 0)}\n"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard()
    )


# =========================================================
# TASKS
# =========================================================

async def show_tasks(callback: CallbackQuery):

    tasks = get_all_tasks()

    if not tasks:

        text = "📋 TASKS\n\nNo tasks found."

    else:

        text = "📋 TASK MANAGEMENT\n\n"

        for task in tasks:

            status = (
                "🟢 Active"
                if task.get("active")
                else "🔴 Inactive"
            )

            text += (
                f"🆔 Task ID: {task.get('id')}\n"
                f"📌 {task.get('title')}\n"
                f"💰 Reward: "
                f"${task.get('reward_usd', 0):.4f}\n"
                f"📡 Type: {task.get('task_type')}\n"
                f"📊 Status: {status}\n\n"
            )

            text += (
                f"/taskstatus "
                f"{task.get('id')} "
                f"{0 if task.get('active') else 1}\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard()
    )


@dp.message(Command("taskstatus"))
async def task_status_command(message: Message):

    user = message.from_user

    if not user or not is_admin(user.id):
        return

    parts = message.text.split()

    if len(parts) != 3:

        await message.answer(
            "Usage:\n"
            "/taskstatus TASK_ID 1\n"
            "/taskstatus TASK_ID 0"
        )

        return

    try:

        task_id = int(parts[1])
        active = bool(int(parts[2]))

        set_task_status(task_id, active)

        await message.answer(
            f"✅ Task {task_id} status updated.\n"
            f"Active: {active}"
        )

    except ValueError:

        await message.answer(
            "❌ Invalid task ID or status."
        )
        # =========================================================
# DEPOSIT WALLETS / NETWORKS
# =========================================================

async def show_wallets(callback: CallbackQuery):

    networks = get_all_networks()

    if not networks:
        await callback.message.edit_text(
            "💳 DEPOSIT WALLETS\n\nNo networks found.",
            reply_markup=back_keyboard()
        )
        return

    text = "💳 DEPOSIT WALLETS\n\n"
    buttons = []

    for network in networks:

        name = network.get("name") or network.get("code") or "Network"
        code = network.get("code") or ""
        address = network.get("address") or "Not set"

        text += (
            f"🌐 {name}\n"
            f"🔑 Code: {code}\n"
            f"💳 Address: {address}\n"
            f"🆔 Network ID: {network.get('id')}\n"
            "──────────────\n"
        )

        buttons.append([
            InlineKeyboardButton(
                text=f"✏️ Change {name}",
                callback_data=f"wallet_change_{code}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="🔙 Back to Admin",
            callback_data="admin_home"
        )
    ])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        )
    )


# =========================================================
# WALLET COMMAND
# =========================================================

@dp.message(Command("wallet"))
async def wallet_command(message: Message):

    user = message.from_user

    if not user or not is_admin(user.id):
        return

    parts = (message.text or "").strip().split()

    if len(parts) < 3:

        await message.answer(
            "❌ সঠিক নিয়মে পাঠাও:\n\n"
            "/wallet NETWORK_CODE NEW_ADDRESS\n\n"
            "উদাহরণ:\n"
            "/wallet USDT_BEP20 0xYourWalletAddress"
        )

        return

    network_code = parts[1].strip().upper()
    address = " ".join(parts[2:]).strip()

    updated = update_network_address(
        network_code,
        address
    )

    if updated:

        await message.answer(
            "✅ Wallet address updated successfully.\n\n"
            f"🌐 Network: {network_code}\n"
            f"💳 Address: {address}"
        )

    else:

        await message.answer(
            "❌ Network not found.\n\n"
            "Available codes:\n"
            "• USDT_TRC20\n"
            "• USDT_BEP20\n"
            "• TON"
        )


# =========================================================
# INLINE WALLET ADDRESS CHANGE
# =========================================================

@dp.callback_query(F.data.startswith("wallet_change_"))
async def wallet_change_callback(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin(callback.from_user.id):

        await callback.answer(
            "❌ Access denied.",
            show_alert=True
        )

        return

    network_code = callback.data.replace(
        "wallet_change_",
        "",
        1
    ).strip().upper()

    await state.update_data(
        network_code=network_code
    )

    await state.set_state(
        WalletAddressState.waiting_for_address
    )

    await callback.message.answer(
        f"✏️ Send the new wallet address for {network_code}.\n\n"
        "Send only the wallet address in your next message."
    )

    await callback.answer()


@dp.message(WalletAddressState.waiting_for_address)
async def receive_wallet_address(
    message: Message,
    state: FSMContext
):

    user = message.from_user

    if not user or not is_admin(user.id):

        await state.clear()
        return

    address = (message.text or "").strip()

    data = await state.get_data()

    network_code = (
        data.get("network_code") or ""
    ).strip().upper()

    if not address or not network_code:

        await state.clear()

        await message.answer(
            "❌ Invalid address. "
            "Try again from Deposit Wallets."
        )

        return

    updated = update_network_address(
        network_code,
        address
    )

    await state.clear()

    if updated:

        await message.answer(
            "✅ Wallet address updated successfully.\n\n"
            f"🌐 Network: {network_code}\n"
            f"💳 Address: {address}"
        )

    else:

        await message.answer(
            "❌ Network not found."
        )


# =========================================================
# NETWORKS
# =========================================================

async def show_networks(callback: CallbackQuery):

    networks = get_all_networks()

    text = "🌐 NETWORKS\n\n"

    for network in networks:

        status = (
            "🟢 Active"
            if network.get("active")
            else "🔴 Inactive"
        )

        text += (
            f"🌐 {network.get('name')}\n"
            f"🔑 Code: {network.get('code')}\n"
            f"📊 Status: {status}\n\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard()
    )


# =========================================================
# WITHDRAWALS
# =========================================================

def get_pending_withdrawals():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            withdrawals.*,
            users.telegram_id,
            users.username,
            users.first_name
        FROM withdrawals
        INNER JOIN users
            ON users.id = withdrawals.user_id
        WHERE withdrawals.status = 'pending'
        ORDER BY withdrawals.id DESC
        LIMIT 20
    """)

    withdrawals = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return withdrawals


async def show_withdrawals(callback: CallbackQuery):

    withdrawals = get_pending_withdrawals()

    if not withdrawals:

        text = "💸 WITHDRAWALS\n\nNo pending withdrawals."

    else:

        text = "💸 PENDING WITHDRAWALS\n\n"

        for item in withdrawals:

            text += (
                f"🆔 Withdrawal ID: {item.get('id')}\n"
                f"👤 User ID: {item.get('telegram_id')}\n"
                f"💰 Amount: ${item.get('amount_usd', 0):.4f}\n"
                f"🌐 Network: {item.get('network_code')}\n"
                f"💳 Wallet: {item.get('wallet_address')}\n\n"
                f"/withdrawal approve {item.get('id')}\n"
                f"/withdrawal reject {item.get('id')}\n"
                "──────────────\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard()
    )
    # =========================================================
# WITHDRAWAL COMMAND
# =========================================================

@dp.message(Command("withdrawal"))
async def withdrawal_command(message: Message):

    user = message.from_user

    if not user or not is_admin(user.id):
        return

    parts = message.text.split()

    if len(parts) != 3:

        await message.answer(
            "Usage:\n"
            "/withdrawal approve ID\n"
            "/withdrawal reject ID"
        )

        return

    action = parts[1].lower()

    try:

        withdrawal_id = int(parts[2])

    except ValueError:

        await message.answer(
            "❌ Invalid withdrawal ID."
        )

        return

    if action not in ["approve", "reject"]:

        await message.answer(
            "❌ Action must be approve or reject."
        )

        return

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM withdrawals WHERE id = ?",
        (withdrawal_id,)
    )

    withdrawal = cursor.fetchone()

    if not withdrawal:

        connection.close()

        await message.answer(
            "❌ Withdrawal not found."
        )

        return

    if withdrawal["status"] != "pending":

        connection.close()

        await message.answer(
            "⚠️ This withdrawal has already been processed."
        )

        return

    new_status = (
        "approved"
        if action == "approve"
        else "rejected"
    )

    cursor.execute("""
        UPDATE withdrawals
        SET status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_status, withdrawal_id))

    connection.commit()
    connection.close()

    await message.answer(
        f"✅ Withdrawal {withdrawal_id} marked as {new_status}."
    )


# =========================================================
# NOTIFICATIONS
# =========================================================

@dp.message(Command("broadcast"))
async def broadcast_command(message: Message):

    user = message.from_user

    if not user or not is_admin(user.id):
        return

    parts = message.text.split(maxsplit=1)

    if len(parts) != 2:

        await message.answer(
            "Usage:\n"
            "/broadcast Your notification message"
        )

        return

    notification_text = parts[1]

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT telegram_id FROM users WHERE is_blocked = 0"
    )

    users = cursor.fetchall()

    connection.close()

    success = 0
    failed = 0

    for item in users:

        telegram_id = item["telegram_id"]

        try:

            await bot.send_message(
                telegram_id,
                f"📢 NEXA Notification\n\n"
                f"{notification_text}"
            )

            success += 1

        except Exception:

            failed += 1

    await message.answer(
        "📢 Broadcast completed.\n\n"
        f"✅ Sent: {success}\n"
        f"❌ Failed: {failed}"
    )


async def show_notifications(callback: CallbackQuery):

    text = (
        "📢 NOTIFICATIONS\n\n"
        "To send a message to all users:\n\n"
        "/broadcast Your message"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard()
    )


# =========================================================
# ADMIN CALLBACK HANDLER
# =========================================================

@dp.callback_query(F.data.startswith("admin_"))
async def admin_callback_handler(callback: CallbackQuery):

    user = callback.from_user

    if not is_admin(user.id):

        await callback.answer(
            "❌ Access denied.",
            show_alert=True
        )

        return

    action = callback.data

    if action == "admin_home":

        await callback.message.edit_text(
            "🔐 NEXA ADMIN PANEL\n\n"
            "Select an option below:",
            reply_markup=admin_keyboard()
        )

    elif action == "admin_users":

        await show_users(callback)

    elif action == "admin_tasks":

        await show_tasks(callback)

    elif action == "admin_wallets":

        await show_wallets(callback)

    elif action == "admin_withdrawals":

        await show_withdrawals(callback)

    elif action == "admin_statistics":

        await show_statistics(callback)

    elif action == "admin_networks":

        await show_networks(callback)

    elif action == "admin_notifications":

        await show_notifications(callback)

    elif action == "admin_close":

        await callback.message.edit_text(
            "✅ Admin Panel closed."
        )

    await callback.answer()


# =========================================================
# MAIN
# =========================================================

async def main():

    logging.info("NEXA Bot is starting...")

    init_db()

    try:

        await dp.start_polling(bot)

    finally:

        await bot.session.close()


if __name__ == "__main__":

    asyncio.run(main())