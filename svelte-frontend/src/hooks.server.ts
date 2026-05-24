import { env } from '$env/dynamic/private';
import type { HandleFetch } from '@sveltejs/kit';

function buildAllowedHosts(): Set<string> {
	const hosts = new Set<string>();
	for (const raw of [env.INTERNAL_API_URL, env.PUBLIC_API_URL]) {
		if (!raw || raw === 'MOCK') continue;
		try {
			hosts.add(new URL(raw).host);
		} catch {
			// ignore malformed URLs
		}
	}
	return hosts;
}

export const handleFetch: HandleFetch = async ({ event, request, fetch }) => {
	const allowedHosts = buildAllowedHosts();
	const url = new URL(request.url);

	// Forward browser cookies only to our own trusted backend hosts.
	if (allowedHosts.size > 0 && allowedHosts.has(url.host)) {
		request.headers.set('cookie', event.request.headers.get('cookie') ?? '');
	}

	return fetch(request);
};
