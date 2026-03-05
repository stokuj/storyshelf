import { apiFetch } from "./api.js";

function hide(el) {
    el?.classList.add("hidden");
}

function show(el) {
    el?.classList.remove("hidden");
}

function createBookCard(book) {
    const article = document.createElement("article");
    article.className = "card bg-base-100 shadow-sm border border-base-300 cursor-pointer hover:shadow-md hover:border-base-content/20 transition-all";
    article.innerHTML = `
        <div class="card-body">
            <h2 class="card-title">${book.title}</h2>
            <p class="text-base-content/80">Autor: ${book.author}</p>
            <div class="card-actions justify-end">
                <span class="badge badge-outline">${book.year}</span>
            </div>
        </div>
    `;
    article.addEventListener("click", () => {
        window.location.href = `?page=book&id=${book.id}`;
    });
    return article;
}

async function loadBooks() {
    const loadingEl = document.getElementById("loading");
    const errorEl = document.getElementById("error");
    const emptyEl = document.getElementById("empty");
    const booksGridEl = document.getElementById("books-grid");

    show(loadingEl);
    hide(errorEl);
    hide(emptyEl);

    try {
        const books = await apiFetch("/api/books");
        booksGridEl.innerHTML = "";

        if (!Array.isArray(books) || books.length === 0) {
            show(emptyEl);
            return;
        }

        books.forEach((book) => {
            booksGridEl.appendChild(createBookCard(book));
        });
    } catch (error) {
        show(errorEl);
    } finally {
        hide(loadingEl);
    }
}

export async function initHome() {
    await loadBooks();
}
