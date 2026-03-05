import { apiFetch, getToken } from "./api.js";

function show(el) { el?.classList.remove("hidden"); }
function hide(el) { el?.classList.add("hidden"); }

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

function renderStars(rating) {
    const starsEl = document.getElementById("book-stars");
    if (!starsEl) return;
    starsEl.innerHTML = "";
    for (let i = 1; i <= 5; i++) {
        const input = document.createElement("input");
        input.type = "radio";
        input.name = "book-rating-display";
        input.className = "mask mask-star-2 bg-orange-400";
        input.disabled = true;
        if (i <= Math.round(rating)) input.checked = true;
        starsEl.appendChild(input);
    }
}

function renderBook(book) {
    document.getElementById("book-title").textContent = book.title;
    document.getElementById("book-author").textContent = `${book.author}`;

    const yearEl = document.getElementById("book-year");
    yearEl.textContent = book.year ? `${book.year} r.` : "";

    const isbnEl = document.getElementById("book-isbn");
    if (book.isbn) {
        isbnEl.textContent = `ISBN: ${book.isbn}`;
    } else {
        hide(isbnEl);
    }

    const pagesEl = document.getElementById("book-pages");
    pagesEl.textContent = book.pageCount ? `${book.pageCount} stron` : "";

    // Gatunki
    const genresWrap = document.getElementById("book-genres-wrap");
    const genresEl = document.getElementById("book-genres");
    if (book.genres && book.genres.length > 0) {
        genresEl.innerHTML = book.genres
            .map(g => `<span class="badge badge-primary badge-outline">${g}</span>`)
            .join("");
        show(genresWrap);
    }

    // Ocena
    const ratingWrap = document.getElementById("book-rating-wrap");
    if (book.rating && book.rating > 0) {
        renderStars(book.rating);
        const count = book.ratingsCount || 0;
        document.getElementById("book-rating-text").textContent =
            `${book.rating.toFixed(1)} / 5 (${count} ${count === 1 ? "ocena" : count < 5 ? "oceny" : "ocen"})`;
        show(ratingWrap);
    }

    // Opis
    const descWrap = document.getElementById("book-description-wrap");
    if (book.description && book.description.trim()) {
        document.getElementById("book-description").textContent = book.description;
        show(descWrap);
    }

    // Tagi
    const tagsWrap = document.getElementById("book-tags-wrap");
    const tagsEl = document.getElementById("book-tags");
    if (book.tags && book.tags.length > 0) {
        tagsEl.innerHTML = book.tags
            .map(t => `<span class="badge badge-outline badge-sm">#${t}</span>`)
            .join("");
        show(tagsWrap);
    }
}

async function getShelfEntry(bookId) {
    try {
        const entries = await apiFetch("/api/me/books");
        if (!Array.isArray(entries)) return null;
        return entries.find(e => e.book.id === bookId) || null;
    } catch {
        return null;
    }
}

async function setupShelfControls(bookId) {
    const actionsEl = document.getElementById("book-actions");
    if (!actionsEl) return;

    let entry = await getShelfEntry(bookId);

    function renderControls() {
        // Usuń poprzednie kontrolki półki (zachowaj link "Wróć")
        actionsEl.querySelectorAll(".shelf-control").forEach(el => el.remove());

        if (entry) {
            // Select statusu
            const select = document.createElement("select");
            select.className = "shelf-control select select-bordered select-sm";
            select.innerHTML = Object.entries(STATUS_LABELS)
                .map(([val, label]) =>
                    `<option value="${val}" ${entry.status === val ? "selected" : ""}>${label}</option>`)
                .join("");

            select.addEventListener("change", async () => {
                select.disabled = true;
                try {
                    entry = await apiFetch(`/api/me/books/${bookId}`, {
                        method: "PUT",
                        body: JSON.stringify({ status: select.value })
                    });
                } catch {
                    // Przywróć poprzednią wartość przy błędzie
                    select.value = entry.status;
                } finally {
                    select.disabled = false;
                }
            });

            // Przycisk usuń
            const removeBtn = document.createElement("button");
            removeBtn.className = "shelf-control btn btn-outline btn-error btn-sm";
            removeBtn.textContent = "Usuń z półki";

            removeBtn.addEventListener("click", async () => {
                removeBtn.disabled = true;
                try {
                    await apiFetch(`/api/me/books/${bookId}`, { method: "DELETE" });
                    entry = null;
                    renderControls();
                } catch {
                    removeBtn.disabled = false;
                }
            });

            actionsEl.appendChild(select);
            actionsEl.appendChild(removeBtn);
        } else {
            // Przycisk dodaj
            const addBtn = document.createElement("button");
            addBtn.className = "shelf-control btn btn-primary btn-sm";
            addBtn.textContent = "Dodaj do półki";

            addBtn.addEventListener("click", async () => {
                addBtn.disabled = true;
                try {
                    entry = await apiFetch(`/api/me/books/${bookId}`, {
                        method: "POST",
                        body: JSON.stringify({ status: "WANT_TO_READ" })
                    });
                    renderControls();
                } catch (err) {
                    if (err.status === 409) {
                        // Już jest — odśwież stan
                        entry = await getShelfEntry(bookId);
                        renderControls();
                    } else {
                        addBtn.disabled = false;
                    }
                }
            });

            actionsEl.appendChild(addBtn);
        }
    }

    renderControls();
}

export async function initBook(session) {
    const params = new URLSearchParams(window.location.search);
    const id = params.get("id");

    const loadingEl = document.getElementById("book-loading");
    const errorEl = document.getElementById("book-error");
    const errorMsgEl = document.getElementById("book-error-msg");
    const contentEl = document.getElementById("book-content");

    if (!id) {
        hide(loadingEl);
        errorMsgEl.textContent = "Nie podano ID książki.";
        show(errorEl);
        return;
    }

    try {
        const book = await apiFetch(`/api/books/${id}`);
        renderBook(book);

        if (session.loggedIn) {
            await setupShelfControls(book.id);
        }

        hide(loadingEl);
        show(contentEl);
    } catch (err) {
        hide(loadingEl);
        if (err.status === 404) {
            errorMsgEl.textContent = "Książka nie została znaleziona.";
        } else {
            errorMsgEl.textContent = "Nie udało się załadować książki.";
        }
        show(errorEl);
    }
}
