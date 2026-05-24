import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { fixtureBooks } from '$lib/api/__fixtures__/books';
import { fixtureCharacters } from '$lib/api/__fixtures__/characters';
import { fixtureRelations } from '$lib/api/__fixtures__/relations';
import { fixtureUser } from '$lib/api/__fixtures__/user';
import { fixtureExtraction } from '$lib/api/__fixtures__/extraction';

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

	if (rest === 'books/1/reviews/') {
		return json(paginate([], Number(url.searchParams.get('page') ?? 1)));
	}

	if (rest === 'books/2/reviews/') {
		return json(paginate([], Number(url.searchParams.get('page') ?? 1)));
	}

	if (rest === 'books/1/characters/') {
		return json(fixtureCharacters);
	}

	if (rest === 'books/1/relations/') {
		return json(fixtureRelations);
	}

	if (rest === 'books/1/ai/extraction/') {
		return json(fixtureExtraction);
	}

	if (rest === 'users/me/') {
		return json(fixtureUser);
	}

	if (rest === 'shelf/') {
		return json([{ book: '1', status: 'WANT_TO_READ', createdAt: '2024-01-01T00:00:00Z' }]);
	}

	return json({});
};
