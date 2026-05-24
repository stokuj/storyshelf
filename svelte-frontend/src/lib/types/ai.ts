import type { BookId } from './book';
import type { Character } from './character';
import type { Relation } from './character';

export interface AIExtraction {
	id: number;
	book_id: BookId;
	status: 'pending' | 'ready' | 'failed';
	created_at: string;
	finished_at: string | null;
	characters: Character[];
	relations: Relation[];
	covered_through: { chapter: number | null; percentage: number };
	confidence_summary: { overall: number; flagged_low: number };
	failure_reason: string | null;
}
