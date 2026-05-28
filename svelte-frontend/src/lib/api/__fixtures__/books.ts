import type { Book } from '$lib/types';

export const fixtureBooks: Book[] = [
	{
		id: 1,
		slug: 'dune',
		title: 'Dune',
		authors: ['Frank Herbert'],
		cover_url: 'https://covers.openlibrary.org/b/id/12170164-L.jpg',
		year: 1965,
		genres: ['Science Fiction', 'Adventure'],
		description:
			"Set on the desert planet Arrakis, Dune is the story of Paul Atreides—who would become known as Muad'Dib—and of a great family's ambition to bring to fruition mankind's most ancient and unattainable dream.",
		page_count: 412,
		avg_rating: 4.5,
		ratings_count: 128,
		characters_count: 8,
		relations_count: 6,
		ai_extraction_status: 'ready'
	},
	{
		id: 2,
		slug: 'project-hail-mary',
		title: 'Project Hail Mary',
		authors: ['Andy Weir'],
		cover_url: 'https://covers.openlibrary.org/b/id/12678411-L.jpg',
		year: 2021,
		genres: ['Science Fiction'],
		description:
			'Ryland Grace is the sole survivor on a desperate, last-chance mission—and if he fails, humanity and the earth itself will perish.',
		page_count: 496,
		avg_rating: 4.7,
		ratings_count: 95,
		characters_count: 0,
		relations_count: 0,
		ai_extraction_status: 'none'
	}
];

export interface FixtureBookCardData {
	id: number;
	slug: string;
	title: string;
	author: string;
	coverUrl: string | null;
	genres: string[];
	avgRating?: number;
}

export const fixtureBookCards: FixtureBookCardData[] = fixtureBooks.map((b) => ({
	id: b.id,
	slug: b.slug,
	title: b.title,
	author: b.authors[0] ?? 'Unknown',
	coverUrl: b.cover_url,
	genres: b.genres,
	avgRating: b.avg_rating
}));
