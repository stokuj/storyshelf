import { apiFetch, clearToken } from "./api.js";

function hide(el) {
    el?.classList.add("hidden");
}

function show(el) {
    el?.classList.remove("hidden");
}

const STATUS_LABELS = {
    WANT_TO_READ: "Want to Read",
    READING: "Reading",
    READ: "Read"
};

const STATUS_BADGE = {
    WANT_TO_READ: "badge-info",
    READING: "badge-warning",
    READ: "badge-success"
};

function createBookCard(entry) {
    const book = entry.book;
    const status = entry.status || "WANT_TO_READ";

    const article = document.createElement("article");
    article.className = "card bg-base-100 shadow-sm border border-base-300 cursor-pointer hover:shadow-md hover:border-base-content/20 transition-all";

    article.innerHTML = `
        <div class="card-body">
            <h2 class="card-title">${book.title}</h2>
            <p class="text-base-content/80">Autor: ${book.author}</p>
            <div class="card-actions justify-between items-center mt-2">
                <span class="badge badge-outline">${book.year}</span>
                <span class="shelf-status-badge badge ${STATUS_BADGE[status]}">${STATUS_LABELS[status]}</span>
            </div>
            <div class="mt-3" onclick="event.stopPropagation()">
                <select class="shelf-select select select-bordered select-xs w-full">
                    ${Object.entries(STATUS_LABELS)
                        .map(([val, label]) =>
                            `<option value="${val}" ${status === val ? "selected" : ""}>${label}</option>`)
                        .join("")}
                </select>
            </div>
        </div>
    `;

    // Klik w kartę → panel książki
    article.addEventListener("click", () => {
        window.location.href = `?page=book&id=${book.id}`;
    });

    // Zmiana statusu przez select
    const select = article.querySelector(".shelf-select");
    select.addEventListener("change", async (e) => {
        e.stopPropagation();
        select.disabled = true;
        const newStatus = select.value;
        try {
            await apiFetch(`/api/me/books/${book.id}`, {
                method: "PUT",
                body: JSON.stringify({ status: newStatus })
            });
            const badge = article.querySelector(".shelf-status-badge");
            badge.className = `shelf-status-badge badge ${STATUS_BADGE[newStatus]}`;
            badge.textContent = STATUS_LABELS[newStatus];
        } catch {
            // Przywróć poprzednią wartość przy błędzie
            select.value = status;
        } finally {
            select.disabled = false;
        }
    });

    return article;
}

export async function initBookshelf() {
    const loadingEl = document.getElementById("bookshelf-loading");
    const errorEl = document.getElementById("bookshelf-error");
    const emptyEl = document.getElementById("bookshelf-empty");
    const gridEl = document.getElementById("bookshelf-grid");

    show(loadingEl);
    hide(errorEl);
    hide(emptyEl);

    try {
        const entries = await apiFetch("/api/me/books");
        gridEl.innerHTML = "";

        if (!Array.isArray(entries) || entries.length === 0) {
            show(emptyEl);
            return;
        }

        entries.forEach((entry) => {
            gridEl.appendChild(createBookCard(entry));
        });
    } catch (error) {
        if (error.status === 401) {
            clearToken();
            window.location.href = "login.html";
            return;
        }
        show(errorEl);
    } finally {
        hide(loadingEl);
    }
}
