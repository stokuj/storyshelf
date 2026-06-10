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

/** GET /api/u/{handle}/shelf/ (PublicShelfEntrySerializer — no id). */
export type PublicShelfEntry = Omit<ShelfEntry, 'id'>;

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

export interface Shelf {
	id: number;
	name: string;
	slug: string;
	description: string;
	is_public: boolean;
	book_count: number;
	/** Present only when the list is fetched with a bookSlug filter; else null. */
	contains_book: boolean | null;
	created_at: string;
	updated_at: string;
}

export interface ShelfDetail extends Shelf {
	books: ShelfBook[];
}

export interface PublicShelf {
	name: string;
	slug: string;
	description: string;
	book_count: number;
	created_at: string;
}

export interface PublicShelfDetail extends PublicShelf {
	books: ShelfBook[];
}

export interface ShelfCreate {
	name: string;
	description?: string;
	is_public?: boolean;
}

export interface ShelfUpdate {
	name?: string;
	description?: string;
	is_public?: boolean;
}
