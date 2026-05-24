import type { BookId } from './book';

export type CharacterId = number;

export type CharacterRole =
	| 'protagonist'
	| 'antagonist'
	| 'supporting'
	| 'minor'
	| 'narrator'
	| 'pov';

export interface Character {
	id: CharacterId;
	name: string;
	also_known_as: string[];
	role: CharacterRole;
	short_bio: string | null;
	long_bio: string | null;
	tags: string[];
	archetype: string | null;
	first_appearance_chapter: number | null;
	source: 'human' | 'ai' | 'ai-verified';
	confidence: number | null;
	book_ids: BookId[];
}

export type RelationKind = 'family' | 'romance' | 'ally' | 'enemy' | 'rival' | 'mentor' | 'other';

export interface Relation {
	id: number;
	book_id: BookId;
	from_character_id: CharacterId;
	to_character_id: CharacterId;
	kind: RelationKind;
	label: string;
	bidirectional: boolean;
	spoiler_chapter: number | null;
	source: 'human' | 'ai' | 'ai-verified';
	confidence: number | null;
}
