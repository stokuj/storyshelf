export type BookId = number;

export interface SerieInfo {
	id: number;
	name: string;
	description: string;
	status: string;
	created_at: string;
}

/** Shape returned by GET /api/books/ (BookListSerializer). */
export interface BookListItem {
	id: number;
	slug: string;
	title: string;
	authors: string[];
	cover_url: string | null;
	year: number | null;
	genres: string[];
	avg_rating: number;
}

/** Shape returned by GET /api/books/{slug}/ (BookDetailSerializer — no id). */
export interface BookDetail {
	slug: string;
	title: string;
	authors: string[];
	cover_url: string | null;
	year: number | null;
	isbn: string | null;
	genres: string[];
	tags: string[];
	description: string | null;
	page_count: number | null;
	avg_rating: number;
	ratings_count: number;
	position_in_series: number | null;
	serie: SerieInfo | null;
	created_at: string;
	updated_at: string;
}
