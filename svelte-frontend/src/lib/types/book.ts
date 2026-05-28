export type BookId = number;

export interface Author {
	id: number;
	name: string;
	slug: string;
}

export interface SerieInfo {
	name: string;
	position_in_series: number | null;
}

export type AIExtractionStatus = 'none' | 'pending' | 'ready' | 'failed';

export interface Book {
	id: number;
	slug: string;
	title: string;
	/** @deprecated use authors[] instead */
	author?: string;
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
	serie: SerieInfo | null;
	characters_count?: number;
	relations_count?: number;
	ai_extraction_status?: AIExtractionStatus;
}
