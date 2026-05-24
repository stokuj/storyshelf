import type { BookId } from './book';

export type UserId = number;
export type Visibility = 'public' | 'friends' | 'private';

export interface User {
	id: UserId;
	handle: string;
	display_name: string;
	email: string;
	email_verified: boolean;
	avatar_url: string | null;
	bio: string | null;
	joined_at: string;
	followers_count: number;
	following_count: number;
}

export interface UserSettings {
	visibility: Visibility;
	show_real_name: 'public' | 'friends' | 'private';
	show_activity: boolean;
	show_followed_characters: boolean;
	ai_learn_from_notes: boolean;
	indexed_by_search_engines: boolean;
	two_factor_enabled: boolean;
	language: string;
	ai_tone: 'scholarly' | 'casual' | 'concise';
	default_spoiler_limit: 'current-chapter' | 'whole-book' | 'no-limit';
	cite_quotes: 'always' | 'on-request' | 'never';
	notification_email: boolean;
	notification_push: boolean;
}

export interface Shelf {
	id: number;
	name: string;
	is_custom: boolean;
	book_ids: BookId[];
}
