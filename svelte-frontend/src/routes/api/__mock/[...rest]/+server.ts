import { error, json } from '@sveltejs/kit';
import { dev } from '$app/environment';
import type { RequestHandler } from './$types';
import { fixtureBooks } from '$lib/api/__fixtures__/books';
import { fixtureUser } from '$lib/api/__fixtures__/user';

function paginate<T>(data: T[], page = 1, perPage = 20) {
	const start = (page - 1) * perPage;
	return {
		data: data.slice(start, start + perPage),
		page,
		per_page: perPage,
		total: data.length
	};
}

export const GET: RequestHandler = ({ params, url }) => {
	if (!dev) throw error(404, 'Not found');

	const rest = params.rest;

	if (rest === 'books/') {
		return json(paginate(fixtureBooks, Number(url.searchParams.get('page') ?? 1)));
	}

	if (rest === 'books/dune/') {
		return json(fixtureBooks[0]);
	}

	if (rest === 'books/project-hail-mary/') {
		return json(fixtureBooks[1]);
	}

	if (rest === 'users/me/') {
		return json(fixtureUser);
	}

	return json({});
};
