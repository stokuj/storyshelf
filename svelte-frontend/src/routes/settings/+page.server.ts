import { fail } from '@sveltejs/kit';
import type { Actions } from './$types';
import { PUBLIC_API_URL } from '$lib/config';

async function apiError(res: Response): Promise<string> {
	const body = await res.json().catch(() => ({}));
	return body.detail ?? body.message ?? `Request failed (${res.status})`;
}

export const actions: Actions = {
	profile: async ({ request, fetch }) => {
		const data = await request.formData();
		const display_name = data.get('display_name') as string;
		const res = await fetch(`${PUBLIC_API_URL}/users/me/`, {
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ display_name }),
			credentials: 'include'
		});
		if (!res.ok) return fail(res.status, { error: await apiError(res) });
		return { success: true };
	},
	handle: async ({ request, fetch }) => {
		const data = await request.formData();
		const handle = data.get('handle') as string;
		if (!handle || handle.length < 3) {
			return fail(400, { error: 'Handle must be at least 3 characters' });
		}
		const res = await fetch(`${PUBLIC_API_URL}/users/me/`, {
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ handle }),
			credentials: 'include'
		});
		if (!res.ok) return fail(res.status, { error: await apiError(res) });
		return { success: true };
	},
	email: async ({ request, fetch }) => {
		const data = await request.formData();
		const email = data.get('email') as string;
		if (!email) {
			return fail(400, { error: 'Email is required' });
		}
		const res = await fetch(`${PUBLIC_API_URL}/users/me/email/`, {
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ new_email: email }),
			credentials: 'include'
		});
		if (!res.ok) return fail(res.status, { error: await apiError(res) });
		return { success: true };
	},
	password: async ({ request, fetch }) => {
		const data = await request.formData();
		const current = data.get('current_password') as string;
		const newPw = data.get('new_password') as string;
		const confirm = data.get('confirm_password') as string;

		if (!current || !newPw) {
			return fail(400, { error: 'Both current and new password are required' });
		}
		if (newPw !== confirm) {
			return fail(400, { error: 'Passwords do not match' });
		}
		if (newPw.length < 8) {
			return fail(400, { error: 'Password must be at least 8 characters' });
		}

		const res = await fetch(`${PUBLIC_API_URL}/users/me/password/`, {
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ current_password: current, new_password: newPw }),
			credentials: 'include'
		});
		if (!res.ok) return fail(res.status, { error: await apiError(res) });
		return { success: true };
	},
	avatar: async ({ request, fetch }) => {
		const data = await request.formData();
		const file = data.get('avatar') as File;
		if (!file || file.size === 0) {
			return fail(400, { error: 'No file provided' });
		}
		const res = await fetch(`${PUBLIC_API_URL}/users/me/avatar/`, {
			method: 'PATCH',
			body: data,
			credentials: 'include'
		});
		if (!res.ok) return fail(res.status, { error: await apiError(res) });
		return { success: true };
	}
};
