export type BookId = number;

export interface Author {
	id: number;
	name: string;
	slug: string;
}

export type AIExtractionStatus = 'none' | 'pending' | 'ready' | 'failed';

export interface Book {
	id: number;
	slug: string;
	title: string;
	author: string;
	cover_url: string | null;
	publication_year: number | null;
	genres: string[];
	description: string | null;
	page_count: number | null;
	avg_rating: number;
	ratings_count: number;
	characters_count: number;
	relations_count: number;
	ai_extraction_status: AIExtractionStatus;
}
