import type { Relation } from '$lib/types';

export const fixtureRelations: Relation[] = [
	{
		id: 1,
		book_id: 1,
		from_character_id: 1,
		to_character_id: 2,
		kind: 'family',
		label: 'son / mother',
		bidirectional: true,
		spoiler_chapter: null,
		source: 'ai',
		confidence: 0.98
	},
	{
		id: 2,
		book_id: 1,
		from_character_id: 1,
		to_character_id: 3,
		kind: 'family',
		label: 'son / father',
		bidirectional: true,
		spoiler_chapter: null,
		source: 'ai',
		confidence: 0.97
	},
	{
		id: 3,
		book_id: 1,
		from_character_id: 1,
		to_character_id: 8,
		kind: 'romance',
		label: 'in love with',
		bidirectional: true,
		spoiler_chapter: 12,
		source: 'ai',
		confidence: 0.85
	},
	{
		id: 4,
		book_id: 1,
		from_character_id: 1,
		to_character_id: 4,
		kind: 'enemy',
		label: 'sworn enemies',
		bidirectional: true,
		spoiler_chapter: null,
		source: 'ai',
		confidence: 0.93
	},
	{
		id: 5,
		book_id: 1,
		from_character_id: 1,
		to_character_id: 5,
		kind: 'ally',
		label: 'friends / mentor',
		bidirectional: true,
		spoiler_chapter: null,
		source: 'ai',
		confidence: 0.9
	},
	{
		id: 6,
		book_id: 1,
		from_character_id: 1,
		to_character_id: 6,
		kind: 'ally',
		label: 'allies',
		bidirectional: true,
		spoiler_chapter: null,
		source: 'ai',
		confidence: 0.89
	}
];
