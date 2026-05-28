import svelteConfig from './svelte.config.js';
import js from '@eslint/js';
import svelte from 'eslint-plugin-svelte';
import tseslint from 'typescript-eslint';
import globals from 'globals';
import svelteParser from 'svelte-eslint-parser';

export default tseslint.config(
	{
		ignores: ['.svelte-kit/', 'build/', 'node_modules/', 'src/lib/types/api.generated.ts']
	},
	js.configs.recommended,
	...tseslint.configs.recommended,
	...svelte.configs['flat/recommended'],
	{
		languageOptions: {
			globals: {
				...globals.browser,
				...globals.node
			}
		}
	},
	{
		files: ['**/*.svelte'],
		languageOptions: {
			parser: svelteParser,
			parserOptions: {
				parser: tseslint.parser,
				svelteConfig
			}
		}
	},
	{
		files: ['**/*.svelte.js', '**/*.svelte.ts'],
		languageOptions: {
			parser: svelteParser,
			parserOptions: {
				svelteConfig
			}
		}
	},
	{
		files: ['src/lib/components/ui/**/*'],
		rules: {
			'@typescript-eslint/no-explicit-any': 'off'
		}
	},
	{
		// Playwright fixtures are used for side effects (e.g. authUser logs in)
		// even when the fixture value itself is not referenced in the test body.
		files: ['e2e/**/*.ts'],
		rules: {
			'@typescript-eslint/no-unused-vars': [
				'error',
				{
					argsIgnorePattern: '^_',
					destructuredArrayIgnorePattern: '^_',
					ignoreRestSiblings: true,
					args: 'none'
				}
			]
		}
	},
	{
		rules: {
			// `resolve()` from $app/paths requires literal route strings,
			// which breaks dynamic URLs (new URL(...)) and variable-based hrefs.
			// SvelteKit resolves paths correctly without the explicit resolve() call.
			'svelte/no-navigation-without-resolve': ['error', { ignoreGoto: true, ignoreLinks: true }]
		}
	}
);
