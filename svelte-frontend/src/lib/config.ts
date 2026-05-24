import { env } from '$env/dynamic/public';
import { env as privateEnv } from '$env/dynamic/private';

export const PUBLIC_API = env.PUBLIC_API_URL ?? '';
export const INTERNAL_API = privateEnv.INTERNAL_API_URL ?? env.PUBLIC_API_URL ?? '';
