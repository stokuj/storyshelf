import type { User, UserSettings } from '$lib/types';

export const fixtureUser: User = {
	id: 1,
	handle: 'demo-reader',
	display_name: 'Demo Reader',
	email: 'demo@storyshelf.dev',
	email_verified: true,
	avatar_url: null,
	bio: 'A demo account for testing Storyshelf features.',
	joined_at: '2024-01-15T00:00:00Z',
	followers_count: 42,
	following_count: 17
};

export const fixtureUserSettings: UserSettings = {
	visibility: 'public',
	show_real_name: 'friends',
	show_activity: true,
	show_followed_characters: true,
	ai_learn_from_notes: false,
	indexed_by_search_engines: true,
	two_factor_enabled: false,
	language: 'en',
	ai_tone: 'scholarly',
	default_spoiler_limit: 'current-chapter',
	cite_quotes: 'always',
	notification_email: true,
	notification_push: false
};
