import { initHome } from "./home.js";
import { apiFetch, clearToken, getToken } from "./api.js";
import { initBookshelf } from "./bookshelf.js";
import { initSettings } from "./settings.js";

const pageContentEl = document.getElementById("page-content");
const navLinksEl = document.getElementById("nav-links");

const pages = {
    home: {
        file: "home.html",
        protected: false,
        init: async () => initHome()
    },
    settings: {
        file: "settings.html",
        protected: true,
        init: async (session) => initSettings(session)
    },
    bookshelf: {
        file: "bookshelf.html",
        protected: true,
        init: async () => initBookshelf()
    }
};

async function getSession() {
    const token = getToken();
    if (!token) {
        return { loggedIn: false, email: null };
    }

    try {
        const me = await apiFetch("/api/auth/me");
        return { loggedIn: true, email: me.email };
    } catch (error) {
        clearToken();
        return { loggedIn: false, email: null };
    }
}

function renderNav(session) {
    const common = '<a href="?page=home" class="btn btn-ghost btn-sm">Home</a>';

    if (session.loggedIn) {
        navLinksEl.innerHTML = `
            ${common}
            <a href="?page=bookshelf" class="btn btn-ghost btn-sm">Bookshelf</a>
            <a href="?page=settings" class="btn btn-ghost btn-sm">Settings</a>
            <button id="logout-btn" class="btn btn-sm">Logout</button>
        `;

        const logoutBtn = document.getElementById("logout-btn");
        logoutBtn?.addEventListener("click", () => {
            clearToken();
            window.location.href = "?page=home";
        });
        return;
    }

    navLinksEl.innerHTML = `
        ${common}
        <a href="login.html" class="btn btn-ghost btn-sm">Logowanie</a>
        <a href="register.html" class="btn btn-ghost btn-sm">Rejestracja</a>
    `;
}

async function loadPage() {
    const params = new URLSearchParams(window.location.search);
    const page = params.get("page") || "home";
    const session = await getSession();
    renderNav(session);

    const pageConfig = pages[page];

    if (!pageConfig) {
        pageContentEl.innerHTML = "<div class=\"alert alert-warning\"><span>Nieznana strona.</span></div>";
        return;
    }

    if (pageConfig.protected && !session.loggedIn) {
        window.location.href = "login.html";
        return;
    }

    const response = await fetch(pageConfig.file);
    if (!response.ok) {
        pageContentEl.innerHTML = "<div class=\"alert alert-error\"><span>Nie udalo sie zaladowac strony.</span></div>";
        return;
    }

    pageContentEl.innerHTML = await response.text();
    await pageConfig.init(session);
}

await loadPage();
