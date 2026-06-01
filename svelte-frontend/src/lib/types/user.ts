export interface User {
	handle: string;
	display_name: string;
	bio: string | null;
	avatar_url: string | null;
	member_since: string;
	profile_public: boolean;
}
