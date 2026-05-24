import { z } from 'zod';

export const changeEmailSchema = z.object({
	new_email: z.string().email()
});

export const changePasswordSchema = z.object({
	current_password: z.string().min(1),
	new_password: z.string().min(8)
});

export const updateProfileSchema = z.object({
	display_name: z.string().min(1).max(100),
	handle: z
		.string()
		.min(3)
		.max(30)
		.regex(/^[a-z0-9_-]+$/),
	bio: z.string().max(500).nullable()
});

export type ChangeEmailSchema = typeof changeEmailSchema;
export type ChangePasswordSchema = typeof changePasswordSchema;
export type UpdateProfileSchema = typeof updateProfileSchema;
