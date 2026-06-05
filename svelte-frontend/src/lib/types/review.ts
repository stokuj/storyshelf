export interface ReviewAuthor {
	handle: string;
	display_name: string;
}

export interface Review {
	id: number;
	body: string;
	author: ReviewAuthor;
	author_rating: number | null;
	created_at: string;
	updated_at: string;
	likes_count: number;
	is_liked: boolean;
}
