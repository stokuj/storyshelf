import { setToken } from "./api.js";

const messageEl = document.getElementById("message");

function showMessage(text) {
    if (messageEl) {
        messageEl.textContent = text;
    }
}

const params = new URLSearchParams(window.location.search);
const token = params.get("token");

if (!token) {
    showMessage("Brak tokena z GitHuba. Wroc do logowania.");
} else {
    setToken(token);
    showMessage("Logowanie udane. Przekierowuje...");
    window.setTimeout(() => {
        window.location.href = "books.html";
    }, 400);
}
