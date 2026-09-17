# =========================================================
# NEXA BOT - BACKEND API
# =========================================================

import hashlib
import hmac
import json
import logging
import os
import time
from urllib.parse import parse_qsl

from aiohttp import web

from config import BOT_TOKEN

from database import (
    init_db,
    get_or_create_user,
    get_user_by_telegram_id,
    get_balance,
    get_active_networks,
    get_network,
    create_deposit,
    create_withdrawal,
    get_user_transactions,
    get_active_tasks,
    add_task,
    get_user_notifications,
    get_referral_count,
    get_active_fees,
    get_setting,
    get_active_user_miner,
    start_mining_session,
    calculate_mining_earning,
)


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("nexa-api")


# =========================================================
# CORS
# =========================================================

@web.middleware
async def cors_middleware(request, handler):
    if request.method == "OPTIONS":
        response = web.Response(status=204)
    else:
        try:
            response = await handler(request)
        except web.HTTPException as error:
            response = error

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = (
        "Content-Type, X-Telegram-Init-Data"
    )
    response.headers["Access-Control-Allow-Methods"] = (
        "GET, POST, OPTIONS"
    )

    return response


# =========================================================
# JSON HELPERS
# =========================================================

def success(data=None, message="OK"):
    return web.json_response({
        "success": True,
        "message": message,
        "data": data
    })


def error(message, status=400):
    return web.json_response({
        "success": False,
        "message": message
    }, status=status)


# =========================================================
# TELEGRAM WEB APP VALIDATION
# =========================================================

def validate_telegram_init_data(init_data: str):
    """
    Validate Telegram WebApp initData using BOT_TOKEN.
    """

    if not init_data:
        return None

    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not configured.")
        return None

    try:
        parsed_data = dict(
            parse_qsl(
                init_data,
                keep_blank_values=True
            )
        )

        received_hash = parsed_data.pop("hash", None)

        if not received_hash:
            return None

        data_check_string = "\n".join(
            f"{key}={value}"
            for key, value in sorted(parsed_data.items())
        )

        secret_key = hmac.new(
            b"WebAppData",
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
            calculated_hash,
            received_hash
        ):
            return None

        auth_date = parsed_data.get("auth_date")

        if auth_date:
            try:
                auth_time = int(auth_date)

                if time.time() - auth_time > 86400:
                    return None

            except ValueError:
                return None

        user_json = parsed_data.get("user")

        if not user_json:
            return None

        telegram_user = json.loads(user_json)

        if not telegram_user.get("id"):
            return None

        return telegram_user

    except Exception as exc:
        logger.exception(
            "Telegram initData validation failed: %s",
            exc
        )

        return None


# =========================================================
# AUTHENTICATION
# =========================================================

def get_authenticated_user(request):
    init_data = request.headers.get(
        "X-Telegram-Init-Data",
        ""
    )

    telegram_user = validate_telegram_init_data(
        init_data
    )

    if not telegram_user:
        return None

    return telegram_user


def require_user(request):
    telegram_user = get_authenticated_user(request)

    if not telegram_user:
        raise web.HTTPUnauthorized(
            text=json.dumps({
                "success": False,
                "message": "Telegram authentication required."
            }),
            content_type="application/json"
        )

    return telegram_user


# =========================================================
# ADMIN AUTHENTICATION
# =========================================================

def get_admin_telegram_id():
    value = os.getenv(
        "ADMIN_TELEGRAM_ID",
        ""
    ).strip()

    if not value:
        return None

    try:
        return int(value)

    except ValueError:
        logger.error(
            "ADMIN_TELEGRAM_ID is invalid."
        )

        return None


def require_admin(request):
    telegram_user = get_authenticated_user(request)

    if not telegram_user:
        raise web.HTTPUnauthorized(
            text=json.dumps({
                "success": False,
                "message": "Telegram authentication required."
            }),
            content_type="application/json"
        )

    admin_id = get_admin_telegram_id()

    if not admin_id:
        raise web.HTTPForbidden(
            text=json.dumps({
                "success": False,
                "message": "Admin account is not configured."
            }),
            content_type="application/json"
        )

    if int(telegram_user["id"]) != admin_id:
        raise web.HTTPForbidden(
            text=json.dumps({
                "success": False,
                "message": "Admin access denied."
            }),
            content_type="application/json"
        )

    return telegram_user


# =========================================================
# HEALTH
# =========================================================

async def health(request):
    return success({
        "service": "NEXA API",
        "status": "online"
    })


async def admin_test(request):
    admin = require_admin(request)

    return success({
        "admin": True,
        "telegram_id": admin["id"],
        "message": "Admin authentication successful."
    })


# =========================================================
# USER
# =========================================================

async def user_me(request):
    telegram_user = require_user(request)

    user = get_or_create_user(
        telegram_id=telegram_user["id"],
        username=telegram_user.get("username"),
        first_name=telegram_user.get("first_name"),
        last_name=telegram_user.get("last_name")
    )

    return success(user)


# =========================================================
# BALANCE
# =========================================================

async def user_balance(request):
    telegram_user = require_user(request)

    balance = get_balance(
        telegram_user["id"]
    )

    if not balance:
        return error(
            "Balance not found.",
            404
        )

    return success(balance)


# =========================================================
# NETWORKS
# =========================================================

async def networks(request):
    return success(
        get_active_networks()
    )


# =========================================================
# SINGLE NETWORK
# =========================================================

async def network_details(request):
    code = request.match_info.get("code")

    if not code:
        return error(
            "Network code is required."
        )

    network = get_network(code)

    if not network:
        return error(
            "Network not found.",
            404
        )

    if not network.get("active"):
        return error(
            "Network is inactive.",
            400
        )

    return success(network)
    # =========================================================
# DEPOSIT
# =========================================================

async def deposit_create(request):
    telegram_user = require_user(request)

    try:
        body = await request.json()
    except Exception:
        return error("Invalid JSON.")

    try:
        amount = float(body.get("amount", 0))
    except (TypeError, ValueError):
        return error("Invalid amount.")

    network_code = str(
        body.get("network_code", "")
    ).strip()

    wallet_address = str(
        body.get("wallet_address", "")
    ).strip()

    transaction_hash = str(
        body.get("transaction_hash", "")
    ).strip()

    if amount <= 0:
        return error(
            "Amount must be greater than 0."
        )

    if not network_code:
        return error(
            "Network is required."
        )

    network = get_network(network_code)

    if not network or not network.get("active"):
        return error(
            "Selected network is unavailable."
        )

    deposit_id = create_deposit(
        telegram_id=telegram_user["id"],
        amount_usd=amount,
        network_code=network_code,
        wallet_address=(
            wallet_address or network.get("address")
        ),
        transaction_hash=transaction_hash or None
    )

    return success(
        {
            "deposit_id": deposit_id,
            "status": "pending"
        },
        "Deposit request submitted."
    )


# =========================================================
# WITHDRAW
# =========================================================

async def withdrawal_create(request):
    telegram_user = require_user(request)

    try:
        body = await request.json()
    except Exception:
        return error("Invalid JSON.")

    try:
        amount = float(body.get("amount", 0))
    except (TypeError, ValueError):
        return error("Invalid amount.")

    network_code = str(
        body.get("network_code", "")
    ).strip()

    wallet_address = str(
        body.get("wallet_address", "")
    ).strip()

    if amount <= 0:
        return error(
            "Amount must be greater than 0."
        )

    minimum_withdrawal = float(
        get_setting(
            "minimum_withdrawal",
            "1"
        )
    )

    if amount < minimum_withdrawal:
        return error(
            f"Minimum withdrawal is ${minimum_withdrawal:.2f}."
        )

    if not network_code:
        return error(
            "Network is required."
        )

    if not wallet_address:
        return error(
            "Wallet address is required."
        )

    network = get_network(network_code)

    if not network or not network.get("active"):
        return error(
            "Selected network is unavailable."
        )

    balance = get_balance(
        telegram_user["id"]
    )

    if not balance:
        return error(
            "Balance not found.",
            404
        )

    current_balance = float(
        balance.get("balance_usd", 0)
    )

    if amount > current_balance:
        return error(
            "Insufficient balance."
        )

    # Balance is deducted only after admin approval.
    withdrawal_id = create_withdrawal(
        telegram_id=telegram_user["id"],
        amount_usd=amount,
        network_code=network_code,
        wallet_address=wallet_address
    )

    return success(
        {
            "withdrawal_id": withdrawal_id,
            "amount_usd": amount,
            "status": "pending"
        },
        "Withdrawal request submitted."
    )


# =========================================================
# TRANSACTION HISTORY
# =========================================================

async def history(request):
    telegram_user = require_user(request)

    transactions = get_user_transactions(
        telegram_user["id"],
        limit=50
    )

    return success(transactions)


# =========================================================
# TASKS
# =========================================================

async def tasks(request):
    return success(
        get_active_tasks()
    )


# =========================================================
# REFERRALS
# =========================================================

async def referrals(request):
    telegram_user = require_user(request)

    count = get_referral_count(
        telegram_user["id"]
    )

    user = get_user_by_telegram_id(
        telegram_user["id"]
    )

    referral_code = None

    if user:
        referral_code = user.get(
            "referral_code"
        )

    return success({
        "referral_code": referral_code,
        "referral_count": count,
        "reward": get_setting(
            "referral_reward",
            "0"
        )
    })


# =========================================================
# NOTIFICATIONS
# =========================================================

async def notifications(request):
    telegram_user = require_user(request)

    items = get_user_notifications(
        telegram_user["id"],
        limit=50
    )

    return success(items)


# =========================================================
# FEES
# =========================================================

async def fees(request):
    return success(
        get_active_fees()
    )


# =========================================================
# SETTINGS
# =========================================================

async def public_settings(request):
    settings = {
        "minimum_withdrawal": get_setting(
            "minimum_withdrawal",
            "1"
        ),
        "mining_enabled": get_setting(
            "mining_enabled",
            "1"
        ),
        "deposit_enabled": get_setting(
            "deposit_enabled",
            "1"
        ),
        "withdrawal_enabled": get_setting(
            "withdrawal_enabled",
            "1"
        ),
        "tasks_enabled": get_setting(
            "tasks_enabled",
            "1"
        ),
        "referrals_enabled": get_setting(
            "referrals_enabled",
            "1"
        ),
        "history_enabled": get_setting(
            "history_enabled",
            "1"
        ),
        "notifications_enabled": get_setting(
            "notifications_enabled",
            "1"
        )
    }

    return success(settings)


# =========================================================
# MINING API
# =========================================================

async def mining_status(request):
    telegram_user = require_user(request)

    user = get_user_by_telegram_id(
        telegram_user["id"]
    )

    if not user:
        return error(
            "User not found.",
            404
        )

    miner = get_active_user_miner(
        user["id"]
    )

    if not miner:
        return success({
            "active": False,
            "message": "No active miner."
        })

    return success({
        "active": True,
        "miner_name": miner["name"],
        "daily_rate_usd": miner["daily_rate_usd"],
        "duration_days": miner["duration_days"]
    })
    
# =========================================================
# =========================================================
# ADMIN TASK API
# =========================================================

async def admin_add_task(request):
    require_admin(request)

    try:
        body = await request.json()
    except Exception:
        return error("Invalid JSON.")

    title = str(body.get("title", "")).strip()
    description = str(body.get("description", "")).strip()
    task_type = str(body.get("task_type", "custom")).strip()
    target = str(body.get("target", "")).strip()

    try:
        reward_usd = float(body.get("reward_usd", 0))
    except (TypeError, ValueError):
        return error("Invalid reward amount.")

    if not title:
        return error("Task title is required.")

    if reward_usd < 0:
        return error("Reward cannot be negative.")

    task_id = add_task(
        title=title,
        description=description,
        reward_usd=reward_usd,
        task_type=task_type,
        target=target
    )

    return success(
        {
            "task_id": task_id,
            "title": title,
            "reward_usd": reward_usd
        },
        "Task added successfully."
    )
# APP
# =========================================================

app = web.Application(
    middlewares=[
        cors_middleware
    ]
)

# =========================================================
# ROUTES
# =========================================================

app.router.add_route("GET", "/api/admin-test", admin_test)
app.router.add_route("GET", "/", health)
app.router.add_route("GET", "/api/health", health)
app.router.add_route("GET", "/api/me", user_me)
app.router.add_route("GET", "/api/balance", user_balance)
app.router.add_route("GET", "/api/mining/status", mining_status)
app.router.add_route("GET", "/api/networks", networks)
app.router.add_route("GET", "/api/networks/{code}", network_details)

app.router.add_route("POST", "/api/deposit", deposit_create)
app.router.add_route("POST", "/api/withdraw", withdrawal_create)

app.router.add_route("GET", "/api/history", history)
app.router.add_route("GET", "/api/tasks", tasks)
app.router.add_route("GET", "/api/referrals", referrals)
app.router.add_route("GET", "/api/notifications", notifications)
app.router.add_route("GET", "/api/fees", fees)
app.router.add_route("GET", "/api/settings", public_settings)

# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", "8080"))
    logger.info("NEXA API starting on port %s", port)
    web.run_app(app, host="0.0.0.0", port=port)