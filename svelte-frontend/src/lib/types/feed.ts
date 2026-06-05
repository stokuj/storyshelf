export interface FeedActor {
	handle: string;
	display_name: string;
	avatar_url: string | null;
}

export interface FeedBook {
	title: string;
	slug: string;
	cover_url: string | null;
}

export interface FeedItem {
	type: 'rating' | 'review' | 'finished';
	timestamp: string;
	actor: FeedActor;
	book: FeedBook;
	rating: number | null;
	body: string | null;
	finish_date: string | null;
}

export interface FeedResponse {
	results: FeedItem[];
	next_before: string | null;
}
