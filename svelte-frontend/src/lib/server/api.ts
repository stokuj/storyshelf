import { PUBLIC_API_URL } from '$lib/config';

/**
 * Base API URL for server-side (SSR / form action) fetches.
 * Inside Docker the browser-facing PUBLIC_API_URL (localhost) is unreachable
 * from the SvelteKit container, so prefer the internal service URL when set.
 */
export function serverApiBase(): string {
	if (typeof process !== 'undefined' && process.env?.INTERNAL_API_URL) {
		return process.env.INTERNAL_API_URL;
	}
	return PUBLIC_API_URL;
}
