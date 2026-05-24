import { INTERNAL_API } from '$lib/config';

export type ApiError = { status: number; detail: string };

async function fetchJson<T>(
	fetchFn: typeof fetch,
	url: string,
	options?: RequestInit
): Promise<{ data: T | null; error: ApiError | null }> {
	try {
		const res = await fetchFn(url, {
			...options,
			headers: {
				'Content-Type': 'application/json',
				...(options?.headers ?? {})
			},
			credentials: 'include'
		});

		if (!res.ok) {
			let detail = res.statusText;
			try {
				const body = await res.json();
				detail = body.detail ?? body.message ?? JSON.stringify(body);
			} catch {
				// non-JSON error body
			}
			return { data: null, error: { status: res.status, detail } };
		}

		// 204 No Content — success with no body (distinct from 200 with empty body).
		if (res.status === 204) {
			return { data: null, error: null };
		}

		const data: T = await res.json();
		return { data, error: null };
	} catch (err) {
		// status: 0 indicates a network error (CORS, timeout, offline), not an HTTP response.
		return { data: null, error: { status: 0, detail: String(err) } };
	}
}

async function attemptTokenRefresh(fetchFn: typeof fetch, base: string): Promise<boolean> {
	try {
		const res = await fetchFn(`${base}/auth/refresh/`, {
			method: 'POST',
			credentials: 'include'
		});
		return res.ok;
	} catch {
		return false;
	}
}

export async function apiFetch<T>(
	fetchFn: typeof fetch,
	path: string,
	options?: RequestInit,
	isServerSide = false
): Promise<{ data: T | null; error: ApiError | null }> {
	const base = isServerSide ? INTERNAL_API : '/api';
	const url = `${base}${path}`;

	// Server-side timeout to prevent hung SSR renders.
	if (isServerSide) {
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), 10_000);
		options = { ...options, signal: controller.signal };
		const result = await fetchJson<T>(fetchFn, url, options);
		clearTimeout(timeoutId);

		if (result.error?.status === 401) {
			const refreshed = await attemptTokenRefresh(fetchFn, base);
			if (refreshed) {
				return fetchJson<T>(fetchFn, url, options);
			}
		}
		return result;
	}

	const result = await fetchJson<T>(fetchFn, url, options);

	if (result.error?.status === 401) {
		const refreshed = await attemptTokenRefresh(fetchFn, base);
		if (refreshed) {
			return fetchJson<T>(fetchFn, url, options);
		}
	}

	return result;
}
