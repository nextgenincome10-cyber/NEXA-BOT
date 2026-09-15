// ======================================================
// NEXA MINI APP
// API CONNECTED VERSION
// ======================================================

const tg = window.Telegram?.WebApp;

// Backend API URL
const API_BASE_URL = "http://127.0.0.1:8080";

const appState = {
    telegramUser: null,
    balance: 0,
    totalEarned: 0,
    totalWithdrawn: 0,
    dailyEarning: 0,
    referralCode: "",
    referralCount: 0,
    referralReward: 0,
    networks: [],
    fees: [],
    settings: {}
};


// ======================================================
// TELEGRAM
// ======================================================

if (tg) {
    tg.ready();
    tg.expand();

    try {
        tg.setHeaderColor("#0b0910");
        tg.setBackgroundColor("#08070b");
    } catch (error) {
        console.log("Telegram theme setup skipped.");
    }
}


function getTelegramUser() {
    if (tg?.initDataUnsafe?.user) {
        return tg.initDataUnsafe.user;
    }

    return null;
}


function getInitData() {
    return tg?.initData || "";
}


function getCurrentUser() {
    return appState.telegramUser;
}


// ======================================================
// API REQUEST
// ======================================================

async function apiRequest(path, options = {}) {

    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {})
    };

    const initData = getInitData();

    if (initData) {
        headers["X-Telegram-Init-Data"] = initData;
    }

    const response = await fetch(
        `${API_BASE_URL}${path}`,
        {
            ...options,
            headers
        }
    );

    let result;

    try {
        result = await response.json();
    } catch (error) {
        throw new Error(
            `API returned HTTP ${response.status}`
        );
    }

    if (!response.ok || !result.success) {
        throw new Error(
            result.message ||
            `Request failed: ${response.status}`
        );
    }

    return result.data;
}


// ======================================================
// LOAD USER
// ======================================================

async function loadUser() {

    try {

        const user = await apiRequest("/api/me");

        if (user) {

            appState.telegramUser = {
                id: user.telegram_id,
                username: user.username,
                first_name: user.first_name,
                last_name: user.last_name
            };
        }

    } catch (error) {

        console.log(
            "User API unavailable:",
            error
        );
    }

    updateProfile();
}


// ======================================================
// LOAD BALANCE
// ======================================================

async function loadBalance() {

    try {

        const balance =
            await apiRequest("/api/balance");

        appState.balance =
            Number(balance.balance_usd || 0);

        appState.totalEarned =
            Number(balance.total_earned_usd || 0);

        appState.totalWithdrawn =
            Number(balance.total_withdrawn_usd || 0);

        updateBalance();
        updateStatistics();

    } catch (error) {

        console.log(
            "Balance API unavailable:",
            error
        );
    }
}


// ======================================================
// UPDATE BALANCE
// ======================================================

function updateBalance() {

    document
        .querySelectorAll("[data-balance]")
        .forEach((element) => {

            element.textContent =
                `$${appState.balance.toFixed(4)}`;

        });
}


// ======================================================
// UPDATE STATISTICS
// ======================================================

function updateStatistics() {

    document
        .querySelectorAll("[data-total-earned]")
        .forEach((element) => {

            element.textContent =
                `$${appState.totalEarned.toFixed(4)}`;

        });


    document
        .querySelectorAll("[data-total-withdrawn]")
        .forEach((element) => {

            element.textContent =
                `$${appState.totalWithdrawn.toFixed(4)}`;

        });


    document
        .querySelectorAll("[data-daily-earning]")
        .forEach((element) => {

            element.textContent =
                `$${appState.dailyEarning.toFixed(4)}`;

        });
}


// ======================================================
// NAVIGATION
// ======================================================

function showPage(page) {

    document
        .querySelectorAll(".page")
        .forEach((section) => {

            section.classList.remove("active");

        });


    const selectedPage =
        document.getElementById(page);


    if (selectedPage) {

        selectedPage.classList.add("active");

    }


    document
        .querySelectorAll("[data-page]")
        .forEach((item) => {

            item.classList.toggle(
                "active",
                item.dataset.page === page &&
                item.classList.contains("nav-item")
            );

        });


    if (page === "deposit") {
        loadNetworks("deposit");
    }


    if (page === "withdraw") {
        loadNetworks("withdraw");
        loadFees();
    }


    if (page === "history") {
        loadHistory();
    }


    if (page === "tasks") {
        loadTasks();
    }


    if (page === "referrals") {
        loadReferrals();
    }


    if (page === "notifications") {
        loadNotifications();
    }


    if (page === "settings") {
        loadSettings();
    }
}


function setupNavigation() {

    document
        .querySelectorAll("[data-page]")
        .forEach((item) => {

            item.addEventListener(
                "click",
                () => {

                    showPage(
                        item.dataset.page
                    );

                }
            );

        });
}// ======================================================
// NETWORKS
// ======================================================

async function loadNetworks(type) {

    const selectId =
        type === "deposit"
            ? "deposit-network"
            : "withdraw-network";

    const select =
        document.getElementById(selectId);

    if (!select) return;

    try {

        const networks =
            await apiRequest("/api/networks");

        appState.networks =
            Array.isArray(networks)
                ? networks
                : [];

        select.innerHTML = "";

        if (!appState.networks.length) {

            select.innerHTML =
                '<option value="">No networks available</option>';

            return;
        }

        appState.networks.forEach((network) => {

            const option =
                document.createElement("option");

            option.value =
                network.code;

            option.textContent =
                network.name;

            select.appendChild(option);

        });

        if (type === "deposit") {
            updateDepositAddress();
        }

    } catch (error) {

        console.log(
            "Network API error:",
            error
        );

        select.innerHTML =
            '<option value="">Unable to load networks</option>';
    }
}


// ======================================================
// DEPOSIT ADDRESS
// ======================================================

function updateDepositAddress() {

    const select =
        document.getElementById(
            "deposit-network"
        );

    const addressElement =
        document.getElementById(
            "deposit-address"
        );

    if (!select || !addressElement) {
        return;
    }

    const network =
        appState.networks.find(
            (item) =>
                item.code === select.value
        );

    if (!network || !network.address) {

        addressElement.textContent =
            "Deposit address has not been configured yet.";

        return;
    }

    addressElement.textContent =
        network.address;
}


function setupNetworkEvents() {

    document
        .getElementById("deposit-network")
        ?.addEventListener(
            "change",
            updateDepositAddress
        );
}


// ======================================================
// DEPOSIT
// ======================================================

async function submitDeposit() {

    const amount =
        Number(
            document.getElementById(
                "deposit-amount"
            )?.value || 0
        );

    const networkCode =
        document.getElementById(
            "deposit-network"
        )?.value || "";

    const txHash =
        document.getElementById(
            "deposit-tx"
        )?.value.trim() || "";


    if (amount <= 0) {

        showMessage(
            "Enter a valid deposit amount.",
            "deposit-message"
        );

        return;
    }


    if (!networkCode) {

        showMessage(
            "Select a deposit network.",
            "deposit-message"
        );

        return;
    }


    try {

        const result =
            await apiRequest(
                "/api/deposit",
                {
                    method: "POST",

                    body: JSON.stringify({
                        amount: amount,
                        network_code: networkCode,
                        transaction_hash: txHash
                    })
                }
            );


        showMessage(
            `Deposit request #${result.deposit_id} submitted for admin review.`,
            "deposit-message"
        );


        document.getElementById(
            "deposit-amount"
        ).value = "";

        document.getElementById(
            "deposit-tx"
        ).value = "";


        await loadHistory();

    } catch (error) {

        showMessage(
            error.message,
            "deposit-message"
        );
    }
}


// ======================================================
// WITHDRAW
// ======================================================

async function submitWithdraw() {

    const amount =
        Number(
            document.getElementById(
                "withdraw-amount"
            )?.value || 0
        );

    const networkCode =
        document.getElementById(
            "withdraw-network"
        )?.value || "";

    const walletAddress =
        document.getElementById(
            "withdraw-address"
        )?.value.trim() || "";


    if (amount <= 0) {

        showMessage(
            "Enter a valid withdrawal amount.",
            "withdraw-message"
        );

        return;
    }


    if (!networkCode) {

        showMessage(
            "Select a withdrawal network.",
            "withdraw-message"
        );

        return;
    }


    if (!walletAddress) {

        showMessage(
            "Enter your wallet address.",
            "withdraw-message"
        );

        return;
    }


    if (amount > appState.balance) {

        showMessage(
            "Insufficient balance.",
            "withdraw-message"
        );

        return;
    }


    try {

        const result =
            await apiRequest(
                "/api/withdraw",
                {
                    method: "POST",

                    body: JSON.stringify({
                        amount: amount,
                        network_code: networkCode,
                        wallet_address: walletAddress
                    })
                }
            );


        showMessage(
            `Withdrawal request #${result.withdrawal_id} submitted for admin review.`,
            "withdraw-message"
        );


        document.getElementById(
            "withdraw-amount"
        ).value = "";

        document.getElementById(
            "withdraw-address"
        ).value = "";


        await loadHistory();

    } catch (error) {

        showMessage(
            error.message,
            "withdraw-message"
        );
    }
}


// ======================================================
// FEES
// ======================================================

async function loadFees() {

    const element =
        document.getElementById(
            "withdraw-fees"
        );

    if (!element) return;


    try {

        const fees =
            await apiRequest("/api/fees");

        appState.fees =
            Array.isArray(fees)
                ? fees
                : [];


        const withdrawalFees =
            appState.fees.filter(
                (fee) =>
                    fee.applies_to === "withdrawal"
            );


        if (!withdrawalFees.length) {

            element.textContent =
                "No withdrawal fee configured.";

            return;
        }


        element.textContent =
            withdrawalFees
                .map((fee) => {

                    if (
                        fee.fee_type ===
                        "percentage"
                    ) {

                        return (
                            `${fee.name}: ` +
                            `${Number(
                                fee.fee_value
                            ).toFixed(2)}%`
                        );
                    }


                    return (
                        `${fee.name}: $` +
                        `${Number(
                            fee.fee_value
                        ).toFixed(4)}`
                    );

                })
                .join(" • ");

    } catch (error) {

        element.textContent =
            "Fee information unavailable.";
    }
}


// ======================================================
// HISTORY
// ======================================================

async function loadHistory() {

    const container =
        document.querySelector(
            "#history .card"
        );

    if (!container) return;


    try {

        const items =
            await apiRequest(
                "/api/history"
            );


        container.innerHTML = "";


        if (!items.length) {

            container.innerHTML =
                '<div class="list-item">' +
                '<div class="list-subtitle">' +
                'No transactions yet.' +
                '</div></div>';

            return;
        }


        items.forEach((item) => {

            const row =
                document.createElement(
                    "div"
                );

            row.className =
                "list-item";


            const positiveTypes = [
                "deposit",
                "mining",
                "earning",
                "referral",
                "task"
            ];


            const isPositive =
                positiveTypes.includes(
                    String(
                        item.type || ""
                    ).toLowerCase()
                );


            row.innerHTML = `
                <div class="list-left">
                    <div class="list-icon">
                        ${isPositive ? "+" : "↓"}
                    </div>

                    <div>
                        <div class="list-title">
                            ${escapeHtml(
                                item.description ||
                                item.type ||
                                "Transaction"
                            )}
                        </div>

                        <div class="list-subtitle">
                            ${escapeHtml(
                                item.created_at || ""
                            )}
                        </div>
                    </div>
                </div>

                <div class="${
                    isPositive
                        ? "amount-positive"
                        : "amount-negative"
                }">
                    ${
                        isPositive ? "+" : "-"
                    }$${Math.abs(
                        Number(
                            item.amount_usd || 0
                        )
                    ).toFixed(4)}
                </div>
            `;


            container.appendChild(row);

        });

    } catch (error) {

        container.innerHTML =
            '<div class="list-item">' +
            '<div class="list-subtitle">' +
            'Unable to load history.' +
            '</div></div>';
    }
}// ======================================================
// TASKS
// ======================================================

async function loadTasks() {

    const container =
        document.querySelector("#tasks .card");

    if (!container) return;

    try {

        const tasks =
            await apiRequest("/api/tasks");

        container.innerHTML = "";

        if (!tasks.length) {

            container.innerHTML =
                '<div class="list-item">' +
                '<div class="list-subtitle">' +
                'No tasks available right now.' +
                '</div></div>';

            return;
        }

        tasks.forEach((task) => {

            const row =
                document.createElement("div");

            row.className = "list-item";

            row.innerHTML = `
                <div class="list-left">
                    <div class="list-icon">✓</div>

                    <div>
                        <div class="list-title">
                            ${escapeHtml(task.title)}
                        </div>

                        <div class="list-subtitle">
                            ${escapeHtml(
                                task.description ||
                                task.task_type ||
                                "Task"
                            )}
                        </div>
                    </div>
                </div>

                <div class="amount-positive">
                    $${Number(
                        task.reward_usd || 0
                    ).toFixed(4)}
                </div>
            `;

            container.appendChild(row);
        });

    } catch (error) {

        container.innerHTML =
            '<div class="list-item">' +
            '<div class="list-subtitle">' +
            'Unable to load tasks.' +
            '</div></div>';
    }
}


// ======================================================
// REFERRALS
// ======================================================

async function loadReferrals() {

    try {

        const data =
            await apiRequest("/api/referrals");

        appState.referralCode =
            data.referral_code || "";

        appState.referralCount =
            Number(data.referral_count || 0);

        appState.referralReward =
            Number(data.reward || 0);


        const codeInput =
            document.querySelector(
                "#referrals input[readonly]"
            );

        if (codeInput) {

            codeInput.value =
                appState.referralCode || "N/A";
        }


        const copyButton =
            document.querySelector(
                "[data-copy-referral]"
            );

        if (copyButton) {

            copyButton.dataset.copyReferral =
                appState.referralCode || "";
        }


        const stats =
            document.querySelectorAll(
                "#referrals .stat-value"
            );


        if (stats[0]) {

            stats[0].textContent =
                appState.referralCount;
        }


        if (stats[1]) {

            stats[1].textContent =
                `$${appState.referralReward.toFixed(4)}`;
        }

    } catch (error) {

        console.log(
            "Referral API error:",
            error
        );
    }
}


// ======================================================
// COPY REFERRAL
// ======================================================

async function copyReferral(button) {

    const code =
        button.dataset.copyReferral || "";

    if (!code) {

        alert(
            "Referral code unavailable."
        );

        return;
    }


    try {

        await navigator.clipboard.writeText(
            code
        );

        const oldText =
            button.textContent;

        button.textContent =
            "Copied!";


        setTimeout(() => {

            button.textContent =
                oldText;

        }, 1500);

    } catch (error) {

        alert(
            `Referral Code: ${code}`
        );
    }
}


// ======================================================
// NOTIFICATIONS
// ======================================================

async function loadNotifications() {

    const container =
        document.getElementById(
            "notifications-list"
        );

    if (!container) return;


    try {

        const items =
            await apiRequest(
                "/api/notifications"
            );

        container.innerHTML = "";


        if (!items.length) {

            container.innerHTML =
                '<div class="list-item">' +
                '<div class="list-subtitle">' +
                'No notifications.' +
                '</div></div>';

            return;
        }


        items.forEach((item) => {

            const row =
                document.createElement(
                    "div"
                );

            row.className =
                "list-item";


            row.innerHTML = `
                <div class="list-left">
                    <div class="list-icon">🔔</div>

                    <div>
                        <div class="list-title">
                            ${escapeHtml(
                                item.title
                            )}
                        </div>

                        <div class="list-subtitle">
                            ${escapeHtml(
                                item.message
                            )}
                        </div>
                    </div>
                </div>
            `;


            container.appendChild(row);

        });

    } catch (error) {

        container.innerHTML =
            '<div class="list-item">' +
            '<div class="list-subtitle">' +
            'Unable to load notifications.' +
            '</div></div>';
    }
}


// ======================================================
// SETTINGS
// ======================================================

async function loadSettings() {

    const element =
        document.getElementById(
            "minimum-withdrawal-setting"
        );


    try {

        const settings =
            await apiRequest(
                "/api/settings"
            );

        appState.settings =
            settings;


        if (element) {

            element.textContent =
                `Minimum withdrawal: $${Number(
                    settings.minimum_withdrawal || 0
                ).toFixed(2)}`;
        }

    } catch (error) {

        if (element) {

            element.textContent =
                "Settings unavailable.";
        }
    }
}


// ======================================================
// PROFILE
// ======================================================

function updateProfile() {

    const user =
        appState.telegramUser;


    const nameElements =
        document.querySelectorAll(
            "[data-profile-name]"
        );


    const usernameElements =
        document.querySelectorAll(
            "[data-profile-username]"
        );


    const idElements =
        document.querySelectorAll(
            "[data-profile-id]"
        );


    const nameElement =
        document.querySelector(
            "[data-user-name]"
        );


    if (!user) {

        if (nameElement) {

            nameElement.textContent =
                "NEXA User";
        }

        return;
    }


    const fullName =
        `${user.first_name || ""} ${user.last_name || ""}`
            .trim();


    if (nameElement) {

        nameElement.textContent =
            fullName || "NEXA User";
    }


    nameElements.forEach((element) => {

        element.textContent =
            fullName || "NEXA User";

    });


    usernameElements.forEach((element) => {

        element.textContent =
            user.username
                ? `@${user.username}`
                : "No username";

    });


    idElements.forEach((element) => {

        element.textContent =
            user.id || "-";

    });
}


// ======================================================
// BUTTONS
// ======================================================

function setupMainButtons() {

    document
        .querySelectorAll(
            "[data-action='deposit']"
        )
        .forEach((button) => {

            button.addEventListener(
                "click",
                () => {
                    showPage("deposit");
                }
            );

        });


    document
        .querySelectorAll(
            "[data-action='withdraw']"
        )
        .forEach((button) => {

            button.addEventListener(
                "click",
                () => {
                    showPage("withdraw");
                }
            );

        });


    document.getElementById(
        "submit-deposit"
    )?.addEventListener(
        "click",
        submitDeposit
    );


    document.getElementById(
        "submit-withdraw"
    )?.addEventListener(
        "click",
        submitWithdraw
    );


    document
        .querySelectorAll(
            "[data-copy-referral]"
        )
        .forEach((button) => {

            button.addEventListener(
                "click",
                () => copyReferral(button)
            );

        });
}


// ======================================================
// TELEGRAM BACK BUTTON
// ======================================================

function setupTelegramBackButton() {

    if (!tg) return;


    try {

        tg.BackButton.onClick(
            () => {

                showPage("home");

                tg.BackButton.hide();

            }
        );

    } catch (error) {

        console.log(
            "Telegram BackButton unavailable."
        );
    }
}


// ======================================================
// HELPERS
// ======================================================

function showMessage(
    message,
    elementId
) {

    const element =
        document.getElementById(
            elementId
        );


    if (!element) return;


    element.textContent =
        message;


    setTimeout(() => {

        if (
            element.textContent ===
            message
        ) {

            element.textContent =
                "";

        }

    }, 5000);
}


function escapeHtml(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


// ======================================================
// START APP
// ======================================================

document.addEventListener(
    "DOMContentLoaded",
    async () => {

        appState.telegramUser =
            getTelegramUser();


        updateProfile();

        updateBalance();

        updateStatistics();


        setupNavigation();

        setupMainButtons();

        setupNetworkEvents();

        setupTelegramBackButton();


        await loadUser();

        await loadBalance();

    }
);