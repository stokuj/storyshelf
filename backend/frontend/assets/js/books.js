import { apiFetch, clearToken } from "./api.js";

const booksBody = document.getElementById("books-body");
const bookForm = document.getElementById("book-form");
const messageEl = document.getElementById("message");
const userInfoEl = document.getElementById("user-info");
const logoutBtn = document.getElementById("logout-btn");

function showMessage(text) {
    if (messageEl) {
        messageEl.textContent = text;
    }
}

function redirectToLogin() {
    window.location.href = "login.html";
}

function createRow(book) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
        <td>${book.id}</td>
        <td>${book.title}</td>
        <td>${book.author}</td>
        <td>${book.year}</td>
        <td><button data-id="${book.id}" class="danger">Usun</button></td>
    `;
    return tr;
}

async function loadBooks() {
    try {
        const books = await apiFetch("/api/books");
        booksBody.innerHTML = "";
        books.forEach((book) => booksBody.appendChild(createRow(book)));
    } catch (error) {
        if (error.status === 401) {
            clearToken();
            redirectToLogin();
            return;
        }
        showMessage(error.body?.message || "Nie udalo sie pobrac listy ksiazek");
    }
}

async function checkSession() {
    try {
        const me = await apiFetch("/api/auth/me");
        userInfoEl.textContent = `Zalogowany: ${me.email}`;
    } catch (error) {
        clearToken();
        redirectToLogin();
    }
}

bookForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(bookForm);
    const payload = {
        title: String(formData.get("title") || ""),
        author: String(formData.get("author") || ""),
        year: Number(formData.get("year") || 0)
    };

    try {
        await apiFetch("/api/books", {
            method: "POST",
            body: JSON.stringify(payload)
        });
        bookForm.reset();
        showMessage("Ksiazka dodana");
        await loadBooks();
    } catch (error) {
        if (error.status === 401) {
            clearToken();
            redirectToLogin();
            return;
        }
        showMessage(error.body?.message || "Nie udalo sie dodac ksiazki");
    }
});

booksBody?.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLButtonElement)) {
        return;
    }

    const id = target.dataset.id;
    if (!id) {
        return;
    }

    try {
        await apiFetch(`/api/books/${id}`, { method: "DELETE" });
        showMessage("Usunieto ksiazke");
        await loadBooks();
    } catch (error) {
        if (error.status === 401) {
            clearToken();
            redirectToLogin();
            return;
        }
        showMessage(error.body?.message || "Nie udalo sie usunac ksiazki");
    }
});

logoutBtn?.addEventListener("click", () => {
    clearToken();
    redirectToLogin();
});

await checkSession();
await loadBooks();
