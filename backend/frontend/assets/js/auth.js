import { apiFetch, clearToken, setToken } from "./api.js";

const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const messageEl = document.getElementById("message");

function showMessage(text, isError = false) {
    if (!messageEl) {
        return;
    }
    messageEl.textContent = text;
    messageEl.className = isError ? "mt-4 text-sm text-error" : "mt-4 text-sm text-success";
}

function extractErrorMessage(error) {
    if (!error || !error.body) {
        return "Brak polaczenia z API.";
    }
    if (error.body.validationErrors) {
        return Object.values(error.body.validationErrors).join("; ");
    }
    return error.body.message || "Blad autoryzacji";
}

async function handleSubmit(event, endpoint) {
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
        showMessage("Sukces. Przekierowuje...");
        window.setTimeout(() => {
            window.location.href = "base.html?page=home";
        }, 400);
    } catch (error) {
        clearToken();
        showMessage(extractErrorMessage(error), true);
    }
}

if (loginForm) {
    loginForm.addEventListener("submit", (event) => handleSubmit(event, "/api/auth/login"));
}

if (registerForm) {
    registerForm.addEventListener("submit", (event) => handleSubmit(event, "/api/auth/register"));
}
