<script lang="ts">
	import { onDestroy } from 'svelte';
	import { toast } from 'svelte-sonner';
	import type { CharacterAnalysisStatus, CharacterSummary } from '$lib/types/character';
	import { fetchCharacters, generateCharacters } from '$lib/api/characters';
	import CharacterCard from './CharacterCard.svelte';

	let {
		bookSlug,
		initialStatus,
		initialCharacters,
		isAuthenticated
	}: {
		bookSlug: string;
		initialStatus: CharacterAnalysisStatus;
		initialCharacters: CharacterSummary[];
		isAuthenticated: boolean;
	} = $props();

	let status = $state<CharacterAnalysisStatus>(initialStatus);
	let characters = $state<CharacterSummary[]>(initialCharacters);
	let starting = $state(false);
	let pollTimer: ReturnType<typeof setTimeout> | undefined;

	const isBusy = $derived(status === 'pending' || status === 'running');

	function stopPolling() {
		if (pollTimer) clearTimeout(pollTimer);
		pollTimer = undefined;
	}

	async function poll() {
		const { data } = await fetchCharacters(fetch, bookSlug);
		if (data) {
			status = data.status;
			characters = data.characters;
		}
		if (status === 'pending' || status === 'running') {
			pollTimer = setTimeout(poll, 3000);
		}
	}

	async function startGeneration() {
		if (starting || isBusy) return;
		starting = true;
		const { data, error } = await generateCharacters(fetch, bookSlug);
		starting = false;
		if (error || !data) {
			toast.error('Could not start generation');
			return;
		}
		status = data.status as CharacterAnalysisStatus;
		stopPolling();
		pollTimer = setTimeout(poll, 3000);
	}

	onDestroy(stopPolling);
</script>

<section class="space-y-4">
	<div class="flex items-center justify-between">
		<h2 class="text-lg font-semibold">Characters</h2>
		{#if isAuthenticated && !isBusy}
			<button
				onclick={startGeneration}
				disabled={starting}
				class="rounded-md border border-rule bg-surface px-3 py-1.5 text-xs font-medium transition-colors hover:bg-paper-2 disabled:opacity-50"
			>
				{characters.length > 0 ? 'Regenerate AI' : 'Generate AI'}
			</button>
		{/if}
	</div>

	{#if isBusy}
		<p class="text-sm text-muted">Generating… this can take up to a minute.</p>
	{:else if status === 'failed' && characters.length === 0}
		<p class="text-sm text-muted">Generation failed.{isAuthenticated ? ' Try again above.' : ''}</p>
	{:else if characters.length > 0}
		<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
			{#each characters as character (character.slug)}
				<CharacterCard {character} {bookSlug} />
			{/each}
		</div>
	{:else}
		<p class="text-sm text-muted">
			No character analysis yet.{isAuthenticated ? '' : ' Sign in to generate it.'}
		</p>
	{/if}
</section>
