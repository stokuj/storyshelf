import type { User } from '$lib/types';

export const fixtureUser: User = {
	id: 1,
	handle: 'demo-reader',
	display_name: 'Demo Reader',
	email: 'demo@storyshelf.dev',
	email_verified: true,
	avatar_url: null,
	bio: 'A demo account for testing Storyshelf features.',
	member_since: '2024-01-15T00:00:00Z'
};
