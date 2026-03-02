const API_BASE_URL = `${window.location.protocol}//${window.location.hostname}:8080`;
const TOKEN_KEY = "springshelf_token";

export function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
}

export async function apiFetch(path, options = {}) {
    const token = getToken();
    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {})
    };

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers
    });

    const body = await response.json().catch(() => null);

    if (!response.ok) {
        throw {
            status: response.status,
            body
        };
    }

    return body;
}
