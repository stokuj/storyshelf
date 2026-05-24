import { z } from 'zod';

export const reviewSchema = z.object({
	rating: z.number().int().min(1).max(5),
	content: z.string().min(10).max(5000)
});

export type ReviewSchema = typeof reviewSchema;
