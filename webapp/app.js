// NEXA Mini App
// Main frontend logic

const tg = window.Telegram?.WebApp;

if (tg) {
    tg.ready();
    tg.expand();
}

// Demo user data
const user = {
    name: "NEXA User",
    balance: 12.4587,
    dailyEarning: 0.0500,
    totalEarned: 18.7421,
    totalWithdrawn: 6.2834
};

// Update balance
function updateBalance() {
    const balanceElements = document.querySelectorAll("[data-balance]");

    balanceElements.forEach((element) => {
        element.textContent = `$${user.balance.toFixed(4)}`;
    });
}

// Navigation
function setupNavigation() {
    const navItems = document.querySelectorAll("[data-page]");

    navItems.forEach((item) => {
        item.addEventListener("click", () => {
            const page = item.dataset.page;

            showPage(page);

            navItems.forEach((nav) => {
                nav.classList.remove("active");
            });

            item.classList.add("active");
        });
    });
}

// Show selected page
function showPage(page) {
    const pages = document.querySelectorAll(".page");

    pages.forEach((section) => {
        section.classList.remove("active");
    });

    const selectedPage = document.getElementById(page);

    if (selectedPage) {
        selectedPage.classList.add("active");
    }
}

// Simple mining counter
function startMiningCounter() {
    const miningElement = document.querySelector("[data-mining]");

    if (!miningElement) return;

    let liveProfit = 0.0000;

    setInterval(() => {
        liveProfit += 0.000001;
        miningElement.textContent = `$${liveProfit.toFixed(6)}`;
    }, 1000);
}

// Deposit button
function setupDepositButton() {
    const buttons = document.querySelectorAll("[data-action='deposit']");

    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            alert("Deposit section will be connected to the backend.");
        });
    });
}

// Withdraw button
function setupWithdrawButton() {
    const buttons = document.querySelectorAll("[data-action='withdraw']");

    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            alert("Withdraw section will be connected to the backend.");
        });
    });
}

// Referral copy button
function setupReferralCopy() {
    const buttons = document.querySelectorAll("[data-copy-referral]");

    buttons.forEach((button) => {
        button.addEventListener("click", async () => {
            const referralCode =
                button.dataset.copyReferral || "NEXA123456";

            try {
                await navigator.clipboard.writeText(referralCode);
                button.textContent = "Copied!";

                setTimeout(() => {
                    button.textContent = "Copy";
                }, 1500);
            } catch (error) {
                alert(`Referral Code: ${referralCode}`);
            }
        });
    });
}

// Telegram user information
function loadTelegramUser() {
    if (!tg?.initDataUnsafe?.user) return;

    const telegramUser = tg.initDataUnsafe.user;

    const nameElement = document.querySelector("[data-user-name]");

    if (nameElement) {
        nameElement.textContent =
            telegramUser.first_name || "NEXA User";
    }
}

// Initialize app
document.addEventListener("DOMContentLoaded", () => {
    updateBalance();
    setupNavigation();
    startMiningCounter();
    setupDepositButton();
    setupWithdrawButton();
    setupReferralCopy();
    loadTelegramUser();
});