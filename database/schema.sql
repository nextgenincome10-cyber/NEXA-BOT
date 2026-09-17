-- =========================================================
-- NEXA BOT DATABASE
-- Complete schema for Mini App + Admin Panel
-- =========================================================

PRAGMA foreign_keys = ON;

-- =========================================================
-- USERS
-- =========================================================

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    referral_code TEXT UNIQUE NOT NULL,
    referred_by INTEGER,
    is_blocked INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (referred_by)
        REFERENCES users(id)
        ON DELETE SET NULL
);

-- =========================================================
-- BALANCES
-- =========================================================

CREATE TABLE IF NOT EXISTS balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    balance_usd REAL DEFAULT 0,
    total_earned_usd REAL DEFAULT 0,
    total_withdrawn_usd REAL DEFAULT 0,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- =========================================================
-- MINERS
-- =========================================================

CREATE TABLE IF NOT EXISTS miners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price_usd REAL NOT NULL,
    daily_rate_usd REAL NOT NULL,
    duration_days INTEGER DEFAULT 30,
    active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- USER MINERS
-- =========================================================

CREATE TABLE IF NOT EXISTS user_miners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    miner_id INTEGER NOT NULL,
    purchased_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    active INTEGER DEFAULT 1,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (miner_id)
        REFERENCES miners(id)
        ON DELETE CASCADE
);

-- =========================================================
-- MINING SESSIONS
-- =========================================================

CREATE TABLE IF NOT EXISTS mining_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_miner_id INTEGER NOT NULL,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    earned_usd REAL DEFAULT 0,

    FOREIGN KEY (user_miner_id)
        REFERENCES user_miners(id)
        ON DELETE CASCADE
);

-- =========================================================
-- NETWORKS / DEPOSIT WALLETS
-- =========================================================

CREATE TABLE IF NOT EXISTS networks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT UNIQUE NOT NULL,
    address TEXT,
    active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- DEPOSITS
-- =========================================================

CREATE TABLE IF NOT EXISTS deposits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount_usd REAL NOT NULL,
    network_code TEXT NOT NULL,
    wallet_address TEXT,
    transaction_hash TEXT,
    status TEXT DEFAULT 'pending',
    admin_note TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- =========================================================
-- WITHDRAWALS
-- =========================================================

CREATE TABLE IF NOT EXISTS withdrawals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount_usd REAL NOT NULL,
    network_code TEXT NOT NULL,
    wallet_address TEXT NOT NULL,
    transaction_hash TEXT,
    status TEXT DEFAULT 'pending',
    admin_note TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- =========================================================
-- TRANSACTIONS
-- =========================================================

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    amount_usd REAL NOT NULL,
    description TEXT,
    reference_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- =========================================================
-- TASKS
-- =========================================================

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    reward_usd REAL DEFAULT 0,
    task_type TEXT DEFAULT 'telegram',
    target TEXT,
    active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- TASK COMPLETIONS
-- =========================================================

CREATE TABLE IF NOT EXISTS task_completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, task_id),

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (task_id)
        REFERENCES tasks(id)
        ON DELETE CASCADE
);

-- =========================================================
-- REFERRALS
-- =========================================================

CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER NOT NULL,
    referred_user_id INTEGER UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (referrer_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (referred_user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- =========================================================
-- REFERRAL REWARDS
-- =========================================================

CREATE TABLE IF NOT EXISTS referral_rewards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER NOT NULL,
    referred_user_id INTEGER NOT NULL,
    amount_usd REAL DEFAULT 0,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (referrer_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (referred_user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- =========================================================
-- NOTIFICATIONS
-- =========================================================

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- =========================================================
-- ADMIN USERS
-- =========================================================

CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    role TEXT DEFAULT 'admin',
    active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- ADMIN SETTINGS
-- =========================================================

CREATE TABLE IF NOT EXISTS admin_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- TAX / FEE SETTINGS
-- Admin can add multiple fees/taxes
-- =========================================================

CREATE TABLE IF NOT EXISTS fees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    fee_type TEXT DEFAULT 'percentage',
    fee_value REAL DEFAULT 0,
    applies_to TEXT DEFAULT 'withdrawal',
    active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- ADMIN LOGS
-- =========================================================

CREATE TABLE IF NOT EXISTS admin_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER,
    action TEXT NOT NULL,
    details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (admin_id)
        REFERENCES admin_users(id)
        ON DELETE SET NULL
);

-- =========================================================
-- DEFAULT MINERS
-- =========================================================

INSERT OR IGNORE INTO miners
    (id, name, description, price_usd, daily_rate_usd, duration_days, active)
VALUES
    (1, 'Starter', 'Starter mining plan', 10, 0.20, 30, 1),
    (2, 'Master', 'Master mining plan', 50, 1.20, 30, 1),
    (3, 'Elite', 'Elite mining plan', 100, 3.00, 30, 1);

-- =========================================================
-- DEFAULT NETWORKS
-- Wallet addresses can be changed from Admin Panel
-- =========================================================

INSERT OR IGNORE INTO networks
    (name, code, address, active)
VALUES
    ('USDT TRC20', 'USDT_TRC20', NULL, 1),
    ('USDT BEP20', 'USDT_BEP20', NULL, 1),
    ('TON', 'TON', NULL, 1);

-- =========================================================
-- DEFAULT SETTINGS
-- =========================================================

INSERT OR IGNORE INTO admin_settings
    (setting_key, setting_value)
VALUES
    ('minimum_withdrawal', '1'),
    ('referral_reward', '0.10'),
    ('mining_enabled', '1'),
    ('deposit_enabled', '1'),
    ('withdrawal_enabled', '1'),
    ('tasks_enabled', '1'),
    ('referrals_enabled', '1'),
    ('history_enabled', '1'),
    ('notifications_enabled', '1');

-- =========================================================
-- DEFAULT FEE
-- =========================================================

INSERT OR IGNORE INTO fees
    (id, name, description, fee_type, fee_value, applies_to, active)
VALUES
    (1, 'Withdrawal Fee', 'Default withdrawal fee', 'percentage', 0, 'withdrawal', 1);