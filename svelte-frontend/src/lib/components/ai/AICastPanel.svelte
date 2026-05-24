<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import { Separator } from '$lib/components/ui/separator';
	import CharacterRow from './CharacterRow.svelte';
	import AIPanel from './AIPanel.svelte';
	import RelationGraphDialog from './RelationGraphDialog.svelte';
	import { runExtraction, getExtraction } from '$lib/api/ai';
	import type { AIExtraction } from '$lib/types';
	import { Sparkles, AlertTriangle, ExternalLink } from 'lucide-svelte';

	interface Props {
		bookId: number;
		slug: string;
		initialExtraction: AIExtraction | null;
	}
	let { bookId, slug, initialExtraction: initExtraction }: Props = $props();

	const initialPanelReady = initExtraction?.status === 'ready';

	type PanelState = 'idle' | 'pending' | 'ready' | 'failed';
	let panelState: PanelState = $state(initialPanelReady ? 'ready' : 'idle');
	let extraction: AIExtraction | null = $state(initExtraction ? structuredClone(initExtraction) : null);
	let errorMessage = $state('');

	async function generate() {
		panelState = 'pending';
		errorMessage = '';
		const { data, error } = await runExtraction(fetch, bookId);
		if (error) {
			errorMessage = error.detail;
			panelState = 'failed';
			return;
		}
		extraction = data;
		panelState = 'ready';
	}

	async function retry() {
		await generate();
	}

	async function refresh() {
		const { data, error } = await getExtraction(fetch, bookId);
		if (error) {
			errorMessage = error.detail;
			return;
		}
		if (data) {
			extraction = data;
			panelState = data.status === 'ready' ? 'ready' : 'pending';
		}
	}

	let showGraph = $state(false);
</script>

<AIPanel title="Meet the cast">
	{#if panelState === 'idle'}
		<p class="text-sm text-accent-ink/80 leading-relaxed mb-4">
			Let AI extract characters and their relationships from this book.
			Characters appear here for you to verify or reject.
		</p>
		<Button variant="default" class="w-full" onclick={generate}>
			<Sparkles class="mr-2 size-4" /> Generate
		</Button>
	{:else if panelState === 'pending'}
		<div class="space-y-3">
			<div class="flex items-center gap-2 text-sm text-accent-ink">
				<span class="inline-block size-2 rounded-full bg-accent animate-pulse"></span>
				Reading the book…
			</div>
			{#each Array(6) as _}
				<div class="flex items-center gap-3">
					<Skeleton class="size-8 rounded-full" />
					<div class="space-y-1 flex-1">
						<Skeleton class="h-3 w-24" />
						<Skeleton class="h-2.5 w-16" />
					</div>
				</div>
			{/each}
		</div>
	{:else if panelState === 'ready' && extraction}
		{#if extraction.confidence_summary.flagged_low > 0}
			<div
				class="flex items-start gap-2 p-2 mb-3 text-xs rounded-md bg-warning/10 text-warning border border-warning/20"
			>
				<AlertTriangle class="size-3 mt-0.5 shrink-0" />
				<span
					>{extraction.confidence_summary.flagged_low} character(s) detected with low confidence.
					They may be one-off mentions.</span
				>
			</div>
		{/if}

		<div class="space-y-2 mb-3">
			{#each extraction.characters.slice(0, 6) as char (char.id)}
				<CharacterRow character={char} {bookId} />
			{/each}
		</div>

		{#if extraction.characters.length > 6}
			<a
				href="/books/{slug}/characters"
				class="text-xs text-accent hover:underline inline-flex items-center gap-1"
			>
				See all ({extraction.characters.length})
				<ExternalLink class="size-3" />
			</a>
		{/if}

		<Separator class="my-3" />

		<div class="flex flex-wrap gap-2">
			<Button variant="outline" size="sm" onclick={() => (showGraph = true)}>
				Open relation graph
			</Button>
			<Button variant="outline" size="sm" onclick={refresh}>
				Refresh
			</Button>
		</div>

		{#if showGraph && extraction}
			<div class="fixed inset-0 z-50 bg-paper/95 backdrop-blur-sm">
				<RelationGraphDialog
					characters={extraction.characters}
					relations={extraction.relations}
					slug={slug}
					onclose={() => (showGraph = false)}
				/>
			</div>
		{/if}
	{:else if panelState === 'failed'}
		<p class="text-sm text-danger mb-3">{errorMessage || 'Extraction failed. Please try again.'}</p>
		<Button variant="outline" size="sm" onclick={retry}>Retry</Button>
	{/if}
</AIPanel>
