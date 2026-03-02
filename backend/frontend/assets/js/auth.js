import { apiFetch, setToken, clearToken } from "./api.js";

const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const messageEl = document.getElementById("message");

function showMessage(text) {
    if (messageEl) {
        messageEl.textContent = text;
    }
}

function extractErrorMessage(error) {
    if (!error || !error.body) {
        return "Brak polaczenia z API (sprawdz czy backend dziala i CORS).";
    }

    if (error.body.validationErrors) {
        return Object.values(error.body.validationErrors).join("; ");
    }

    return error.body.message || "Blad autoryzacji";
}

async function handleAuthSubmit(event, endpoint) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload = {
        email: String(formData.get("email") || ""),
        password: String(formData.get("password") || "")
    };

    try {
        const data = await apiFetch(endpoint, {
            method: "POST",
            body: JSON.stringify(payload)
        });
        setToken(data.token);
        showMessage("Zalogowano pomyslnie. Przekierowuje...");
        window.setTimeout(() => {
            window.location.href = "books.html";
        }, 500);
    } catch (error) {
        clearToken();
        showMessage(extractErrorMessage(error));
    }
}

if (loginForm) {
    loginForm.addEventListener("submit", (event) => handleAuthSubmit(event, "/api/auth/login"));
}

if (registerForm) {
    registerForm.addEventListener("submit", (event) => handleAuthSubmit(event, "/api/auth/register"));
}
