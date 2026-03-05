import { apiFetch, getToken } from "./api.js";

function show(el) { el?.classList.remove("hidden"); }
function hide(el) { el?.classList.add("hidden"); }

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

async function isOnShelf(bookId) {
    try {
        const books = await apiFetch("/api/me/books");
        return Array.isArray(books) && books.some(b => b.id === bookId);
    } catch {
        return false;
    }
}

async function setupShelfButton(bookId) {
    const btn = document.getElementById("btn-shelf");
    if (!btn) return;

    const onShelf = await isOnShelf(bookId);

    function setShelfState(added) {
        if (added) {
            btn.textContent = "Usuń z półki";
            btn.className = "btn btn-outline btn-sm";
        } else {
            btn.textContent = "Dodaj do półki";
            btn.className = "btn btn-primary btn-sm";
        }
    }

    setShelfState(onShelf);
    show(btn);

    let currentState = onShelf;

    btn.addEventListener("click", async () => {
        btn.disabled = true;
        try {
            if (currentState) {
                await apiFetch(`/api/me/books/${bookId}`, { method: "DELETE" });
                currentState = false;
            } else {
                await apiFetch(`/api/me/books/${bookId}`, { method: "POST" });
                currentState = true;
            }
            setShelfState(currentState);
        } catch (err) {
            // Jeśli conflict (409) — książka już jest, odśwież stan
            if (err.status === 409) {
                currentState = true;
                setShelfState(true);
            }
        } finally {
            btn.disabled = false;
        }
    });
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

        // Pokaż przycisk półki tylko zalogowanym
        if (session.loggedIn) {
            await setupShelfButton(book.id);
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
