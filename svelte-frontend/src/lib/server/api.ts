import { internalApiBase } from '$lib/config';

/**
 * Base API URL for server-side (SSR / form action) fetches.
 * Thin re-export of the shared resolver so server modules keep a stable import.
 */
export function serverApiBase(): string {
	return internalApiBase();
}
