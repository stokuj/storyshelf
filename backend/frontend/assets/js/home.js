import { apiFetch } from "./api.js";

const loadingEl = document.getElementById("loading");
const errorEl = document.getElementById("error");
const emptyEl = document.getElementById("empty");
const booksGridEl = document.getElementById("books-grid");

function hide(el) {
    el?.classList.add("hidden");
}

function show(el) {
    el?.classList.remove("hidden");
}

function createBookCard(book) {
    const article = document.createElement("article");
    article.className = "card bg-base-100 shadow-sm border border-base-300";
    article.innerHTML = `
        <div class="card-body">
            <h2 class="card-title">${book.title}</h2>
            <p class="text-base-content/80">Autor: ${book.author}</p>
            <div class="card-actions justify-end">
                <span class="badge badge-outline">${book.year}</span>
            </div>
        </div>
    `;
    return article;
}

async function loadBooks() {
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

await loadBooks();
