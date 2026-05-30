export type ShelfStatus = 'WANT_TO_READ' | 'READING' | 'READ';

export interface ShelfBook {
	slug: string;
	title: string;
	cover_url: string | null;
	authors: string[];
	genres: string[];
	avg_rating: number;
	page_count: number | null;
}

export interface ShelfEntry {
	id: number;
	status: ShelfStatus;
	start_date: string | null;
	finish_date: string | null;
	current_page: number | null;
	user_rating: number | null;
	book: ShelfBook;
}

/** ShelfEntry augmented (client-side) with the rating row id, for delete/un-rate. */
export interface ShelfEntryWithRating extends ShelfEntry {
	rating_id: number | null;
}

export interface ShelfEntryUpdate {
	status?: ShelfStatus;
	start_date?: string | null;
	finish_date?: string | null;
	current_page?: number | null;
}

export interface RatingResponse {
	id: number;
	book_slug: string;
	rating: number;
}
