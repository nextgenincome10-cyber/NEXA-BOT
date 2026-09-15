// ======================================================
// NEXA MINI APP
// Telegram WebApp Frontend
// ======================================================

const tg = window.Telegram?.WebApp;

// ------------------------------------------------------
// Telegram WebApp Initialize
// ------------------------------------------------------

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


// ------------------------------------------------------
// App State
// ------------------------------------------------------

const appState = {
    telegramUser: null,

    balance: 12.4587,
    dailyEarning: 0.0500,
    totalEarned: 18.7421,
    totalWithdrawn: 6.2834,

    liveProfit: 0.000003
};


// ------------------------------------------------------
// Get Telegram User
// ------------------------------------------------------

function getTelegramUser() {

    if (
        tg &&
        tg.initDataUnsafe &&
        tg.initDataUnsafe.user
    ) {
        return tg.initDataUnsafe.user;
    }

    return null;
}


// ------------------------------------------------------
// Load Telegram User Information
// ------------------------------------------------------

function loadTelegramUser() {

    const telegramUser = getTelegramUser();

    appState.telegramUser = telegramUser;

    const nameElement =
        document.querySelector("[data-user-name]");

    if (!nameElement) {
        return;
    }

    if (telegramUser) {

        const firstName =
            telegramUser.first_name || "";

        const lastName =
            telegramUser.last_name || "";

        const fullName =
            `${firstName} ${lastName}`.trim();

        nameElement.textContent =
            fullName || "NEXA User";

    } else {

        nameElement.textContent = "NEXA User";
    }
}


// ------------------------------------------------------
// Get Telegram User ID
// ------------------------------------------------------

function getTelegramUserId() {

    if (appState.telegramUser) {
        return appState.telegramUser.id;
    }

    return null;
}


// ------------------------------------------------------
// Update Balance
// ------------------------------------------------------

function updateBalance() {

    const balanceElements =
        document.querySelectorAll("[data-balance]");

    balanceElements.forEach((element) => {

        element.textContent =
            `$${appState.balance.toFixed(4)}`;

    });
}


// ------------------------------------------------------
// Update Statistics
// ------------------------------------------------------

function updateStatistics() {

    const totalEarnedElements =
        document.querySelectorAll("[data-total-earned]");

    totalEarnedElements.forEach((element) => {

        element.textContent =
            `$${appState.totalEarned.toFixed(4)}`;

    });


    const withdrawnElements =
        document.querySelectorAll("[data-total-withdrawn]");

    withdrawnElements.forEach((element) => {

        element.textContent =
            `$${appState.totalWithdrawn.toFixed(4)}`;

    });


    const dailyElements =
        document.querySelectorAll("[data-daily-earning]");

    dailyElements.forEach((element) => {

        element.textContent =
            `$${appState.dailyEarning.toFixed(4)}`;

    });
}


// ------------------------------------------------------
// Live Mining Counter
// ------------------------------------------------------

function startMiningCounter() {

    const miningElement =
        document.querySelector("[data-mining]");

    if (!miningElement) {
        return;
    }

    let liveProfit =
        appState.liveProfit;


    setInterval(() => {

        liveProfit += 0.000001;

        miningElement.textContent =
            `$${liveProfit.toFixed(6)}`;

    }, 1000);
}


// ------------------------------------------------------
// Page Navigation
// ------------------------------------------------------

function setupNavigation() {

    const navItems =
        document.querySelectorAll("[data-page]");


    navItems.forEach((item) => {

        item.addEventListener("click", () => {

            const page =
                item.dataset.page;

            showPage(page);


            navItems.forEach((nav) => {

                nav.classList.remove("active");

            });


            item.classList.add("active");

        });

    });
}


// ------------------------------------------------------
// Show Page
// ------------------------------------------------------

function showPage(page) {

    const pages =
        document.querySelectorAll(".page");


    pages.forEach((section) => {

        section.classList.remove("active");

    });


    const selectedPage =
        document.getElementById(page);


    if (selectedPage) {

        selectedPage.classList.add("active");

    }
}


// ------------------------------------------------------
// Deposit Button
// ------------------------------------------------------

function setupDepositButton() {

    const buttons =
        document.querySelectorAll(
            "[data-action='deposit']"
        );


    buttons.forEach((button) => {

        button.addEventListener("click", () => {

            showPage("deposit");

        });

    });
}


// ------------------------------------------------------
// Withdraw Button
// ------------------------------------------------------

function setupWithdrawButton() {

    const buttons =
        document.querySelectorAll(
            "[data-action='withdraw']"
        );


    buttons.forEach((button) => {

        button.addEventListener("click", () => {

            showPage("withdraw");

        });

    });
}


// ------------------------------------------------------
// Referral Copy
// ------------------------------------------------------

function setupReferralCopy() {

    const buttons =
        document.querySelectorAll(
            "[data-copy-referral]"
        );


    buttons.forEach((button) => {

        button.addEventListener(
            "click",
            async () => {

                const referralCode =
                    button.dataset.copyReferral ||
                    "NEXA123456";


                try {

                    await navigator.clipboard.writeText(
                        referralCode
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
                        `Referral Code: ${referralCode}`
                    );

                }

            }
        );

    });
}


// ------------------------------------------------------
// Profile Information
// ------------------------------------------------------

function updateProfile() {

    const telegramUser =
        appState.telegramUser;


    if (!telegramUser) {
        return;
    }


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


    const firstName =
        telegramUser.first_name || "";


    const lastName =
        telegramUser.last_name || "";


    const fullName =
        `${firstName} ${lastName}`.trim();


    nameElements.forEach((element) => {

        element.textContent =
            fullName || "NEXA User";

    });


    usernameElements.forEach((element) => {

        element.textContent =
            telegramUser.username
                ? `@${telegramUser.username}`
                : "No username";

    });


    idElements.forEach((element) => {

        element.textContent =
            telegramUser.id || "-";

    });
}


// ------------------------------------------------------
// Telegram Main Button
// ------------------------------------------------------

function setupTelegramMainButton() {

    if (!tg) {
        return;
    }

    try {

        tg.MainButton.hide();

    } catch (error) {

        console.log(
            "Telegram MainButton not available."
        );

    }
}


// ------------------------------------------------------
// Telegram Back Button
// ------------------------------------------------------

function setupTelegramBackButton() {

    if (!tg) {
        return;
    }


    try {

        tg.BackButton.onClick(() => {

            showPage("home");

        });

    } catch (error) {

        console.log(
            "Telegram BackButton not available."
        );

    }
}


// ------------------------------------------------------
// Send Data To Telegram
// ------------------------------------------------------

function sendTelegramData(data) {

    if (!tg) {
        return;
    }


    try {

        tg.sendData(
            JSON.stringify(data)
        );

    } catch (error) {

        console.log(
            "Telegram sendData unavailable."
        );

    }
}


// ------------------------------------------------------
// Get User Information
// ------------------------------------------------------

function getCurrentUser() {

    const user =
        appState.telegramUser;


    if (!user) {

        return {
            id: null,
            username: null,
            first_name: null,
            last_name: null
        };

    }


    return {

        id: user.id || null,

        username:
            user.username || null,

        first_name:
            user.first_name || null,

        last_name:
            user.last_name || null

    };
}


// ------------------------------------------------------
// Console Information
// ------------------------------------------------------

function showTelegramDebugInfo() {

    const user =
        getCurrentUser();


    console.log(
        "================================"
    );

    console.log(
        "NEXA Telegram User"
    );

    console.log(
        "================================"
    );

    console.log(
        "User ID:",
        user.id
    );

    console.log(
        "Username:",
        user.username
    );

    console.log(
        "First Name:",
        user.first_name
    );

    console.log(
        "Last Name:",
        user.last_name
    );

    console.log(
        "================================"
    );
}


// ------------------------------------------------------
// App Initialization
// ------------------------------------------------------

document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadTelegramUser();

        updateBalance();

        updateStatistics();

        updateProfile();

        setupNavigation();

        startMiningCounter();

        setupDepositButton();

        setupWithdrawButton();

        setupReferralCopy();

        setupTelegramMainButton();

        setupTelegramBackButton();

        showTelegramDebugInfo();

    }
);