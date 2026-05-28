import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
	testDir: './e2e',
	globalSetup: './e2e/global-setup.ts',
	timeout: 30_000,
	expect: { timeout: 10_000 },
	fullyParallel: false,
	retries: process.env.CI ? 1 : 0,
	workers: undefined,
	reporter: 'list',
	use: {
		baseURL: 'http://localhost:5174',
		// Disable traces in CI to avoid capturing JWT tokens/passwords in artifacts.
		// Use --trace on locally for debugging flaky tests.
		trace: process.env.CI ? 'off' : 'on-first-retry'
	},
	projects: [
		{
			name: 'chromium',
			use: { ...devices['Desktop Chrome'] }
		}
	],
	webServer: {
		command: 'npm run dev',
		port: 5174,
		reuseExistingServer: true
	}
});
