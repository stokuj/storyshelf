import type { AIExtraction } from '$lib/types';
import { fixtureCharacters } from './characters';
import { fixtureRelations } from './relations';

export const fixtureExtraction: AIExtraction = {
	id: 1,
	book_id: 1,
	status: 'ready',
	created_at: '2024-06-01T10:00:00Z',
	finished_at: '2024-06-01T10:05:00Z',
	characters: fixtureCharacters,
	relations: fixtureRelations,
	covered_through: { chapter: 22, percentage: 60 },
	confidence_summary: { overall: 0.88, flagged_low: 1 },
	failure_reason: null
};
