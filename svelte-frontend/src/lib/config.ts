import { env } from '$env/dynamic/public';

export const PUBLIC_API_URL = env.PUBLIC_API_URL ?? '';

/**
 * API base URL for server-side fetches (SSR / form actions / server endpoints).
 * Inside Docker the browser-facing PUBLIC_API_URL is unreachable from the
 * SvelteKit container, so prefer the internal service URL when set. Reads
 * process.env directly (guarded) to avoid statically importing
 * $env/dynamic/private, which would break client-side bundling.
 */
export function internalApiBase(): string {
	if (typeof process !== 'undefined' && process.env?.INTERNAL_API_URL) {
		return process.env.INTERNAL_API_URL;
	}
	return PUBLIC_API_URL;
}
