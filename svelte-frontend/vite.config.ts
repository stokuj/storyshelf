import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

// Client-side code calls a same-origin `/api` (see docs/decisions/ADR-002).
// In prod, Caddy reverse-proxies `/api/*` to Django; in dev we mirror that here
// so the dev server (local `npm run dev` and the Docker `svelte` container) routes
// `/api` to Django. Dev-only: `server.proxy` does not affect the adapter-node build.
const API_TARGET = (process.env.INTERNAL_API_URL ?? 'http://localhost:8000/api').replace(
	/\/api\/?$/,
	''
);

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		port: 5174,
		host: true,
		proxy: {
			'/api': {
				target: API_TARGET,
				changeOrigin: true
			}
		}
	}
});
