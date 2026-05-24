import { z } from 'zod';

export const aiPreferencesSchema = z.object({
	ai_tone: z.enum(['scholarly', 'casual', 'concise']),
	default_spoiler_limit: z.enum(['current-chapter', 'whole-book', 'no-limit']),
	cite_quotes: z.enum(['always', 'on-request', 'never'])
});

export const visibilitySchema = z.object({
	visibility: z.enum(['public', 'friends', 'private']),
	show_real_name: z.enum(['public', 'friends', 'private']),
	show_activity: z.boolean(),
	show_followed_characters: z.boolean(),
	ai_learn_from_notes: z.boolean(),
	indexed_by_search_engines: z.boolean()
});

export type AIPreferencesSchema = typeof aiPreferencesSchema;
export type VisibilitySchema = typeof visibilitySchema;
