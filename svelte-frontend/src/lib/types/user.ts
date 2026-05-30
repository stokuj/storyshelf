export type UserId = number;

export interface User {
	id: UserId;
	handle: string;
	display_name: string;
	email: string;
	email_verified: boolean;
	avatar_url: string | null;
	bio: string | null;
	member_since: string;
}
