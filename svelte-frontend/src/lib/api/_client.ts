import { INTERNAL_API } from '$lib/config';

export type ApiError = { status: number; detail: string };

export async function apiFetch<T>(
	fetchFn: typeof fetch,
	path: string,
	options?: RequestInit,
	isServerSide = false
): Promise<{ data: T | null; error: ApiError | null }> {
	const base = isServerSide ? INTERNAL_API : '/api';
	const url = `${base}${path}`;

	try {
		const res = await fetchFn(url, {
			headers: {
				'Content-Type': 'application/json',
				...(options?.headers ?? {})
			},
			credentials: 'include',
			...options
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

		if (res.status === 204) {
			return { data: null, error: null };
		}

		const data: T = await res.json();
		return { data, error: null };
	} catch (err) {
		return { data: null, error: { status: 0, detail: String(err) } };
	}
}
