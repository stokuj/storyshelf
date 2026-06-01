import type { RequestHandler } from './$types';
import { serverApiBase } from '$lib/server/api';

// Proxies the authenticated ZIP export from the backend so the browser can
// download it directly. Cookies are forwarded to the backend by handleFetch
// (see src/hooks.server.ts). Backend endpoint is POST and returns application/zip.
export const GET: RequestHandler = async ({ fetch }) => {
	const res = await fetch(`${serverApiBase()}/users/me/export/`, {
		method: 'POST',
		credentials: 'include'
	});

	if (!res.ok) {
		return new Response(`Export failed (${res.status})`, { status: res.status });
	}

	return new Response(res.body, {
		status: 200,
		headers: {
			'Content-Type': res.headers.get('Content-Type') ?? 'application/zip',
			'Content-Disposition':
				res.headers.get('Content-Disposition') ?? 'attachment; filename="storyshelf-export.zip"'
		}
	});
};
