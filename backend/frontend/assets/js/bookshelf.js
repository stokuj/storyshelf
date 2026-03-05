import { apiFetch, clearToken } from "./api.js";

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

export async function initBookshelf() {
    const loadingEl = document.getElementById("bookshelf-loading");
    const errorEl = document.getElementById("bookshelf-error");
    const emptyEl = document.getElementById("bookshelf-empty");
    const gridEl = document.getElementById("bookshelf-grid");

    show(loadingEl);
    hide(errorEl);
    hide(emptyEl);

    try {
        const books = await apiFetch("/api/me/books");
        gridEl.innerHTML = "";

        if (!Array.isArray(books) || books.length === 0) {
            show(emptyEl);
            return;
        }

        books.forEach((book) => {
            gridEl.appendChild(createBookCard(book));
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
