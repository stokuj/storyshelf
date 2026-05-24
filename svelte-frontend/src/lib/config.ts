import { env } from '$env/dynamic/private';
import { PUBLIC_API_URL } from '$env/static/public';

export const PUBLIC_API = PUBLIC_API_URL;
export const INTERNAL_API = env.INTERNAL_API_URL ?? PUBLIC_API_URL;
