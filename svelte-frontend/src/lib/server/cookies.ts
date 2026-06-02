import { dev } from '$app/environment';
import type { Cookies } from '@sveltejs/kit';

/**
 * Forwards Set-Cookie headers from a backend response to the browser.
 * Correctly parses Max-Age, Path, SameSite and overrides Secure based on environment.
 */
export function forwardSetCookies(response: Response, cookies: Cookies): void {
	for (const cookieStr of response.headers.getSetCookie()) {
		const parts = cookieStr.split(';').map((p) => p.trim());
		const nameValue = parts[0];
		const eqIdx = nameValue.indexOf('=');
		if (eqIdx <= 0) continue;

		const name = nameValue.slice(0, eqIdx);
		const value = nameValue.slice(eqIdx + 1);

		let path = '/';
		let maxAge: number | undefined;
		let sameSite: 'lax' | 'strict' | 'none' = 'lax';
		let httpOnly = false;

		for (const attr of parts.slice(1)) {
			const lower = attr.toLowerCase();
			if (lower === 'httponly') {
				httpOnly = true;
			} else if (lower.startsWith('max-age=')) {
				const parsed = parseInt(attr.slice(8), 10);
				if (!isNaN(parsed)) maxAge = parsed;
			} else if (lower.startsWith('path=')) {
				path = attr.slice(5) || '/';
			} else if (lower.startsWith('samesite=')) {
				const val = attr.slice(9).toLowerCase();
				if (val === 'strict' || val === 'lax' || val === 'none') sameSite = val;
			}
		}

		cookies.set(name, value, {
			path,
			httpOnly,
			secure: !dev,
			sameSite,
			...(maxAge !== undefined ? { maxAge } : {})
		});
	}
}
