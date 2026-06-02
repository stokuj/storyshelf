export type BookId = number;

export interface Author {
	id: number;
	name: string;
	slug: string;
}

export interface SerieInfo {
	id: number;
	name: string;
	description: string;
	status: string;
	created_at: string;
}

export interface Book {
	id: number;
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
}
