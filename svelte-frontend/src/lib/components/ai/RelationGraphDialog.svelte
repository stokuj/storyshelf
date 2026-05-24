<script lang="ts">
	import type { Character, Relation } from '$lib/types';
	import { X } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';

	interface Props {
		characters: Character[];
		relations: Relation[];
		slug: string;
		onclose: () => void;
	}
	let { characters, relations, slug: _slug, onclose }: Props = $props();

	const relationColors: Record<string, string> = {
		family: 'var(--color-rel-family)',
		romance: 'var(--color-rel-romance)',
		ally: 'var(--color-rel-ally)',
		enemy: 'var(--color-rel-enemy)',
		rival: 'var(--color-rel-enemy)',
		mentor: 'var(--color-rel-ally)',
		other: 'currentColor'
	};

	function charName(id: number): string {
		return characters.find((c) => c.id === id)?.name ?? `Character #${id}`;
	}

	let activeFilter = $state('');
	let filteredRelations = $derived(
		activeFilter ? relations.filter((r) => r.kind === activeFilter) : relations
	);
</script>

<div class="w-full h-full flex flex-col p-6">
	<div class="flex items-center justify-between mb-4">
		<h2 class="font-display text-2xl font-medium">Relation Graph</h2>
		<Button variant="ghost" size="icon" onclick={onclose}>
			<X class="size-5" />
		</Button>
	</div>

	<div class="flex flex-wrap gap-1.5 mb-4">
		<button
			class="px-2.5 py-0.5 rounded-full text-xs font-medium transition-colors"
			class:bg-ink={activeFilter === ''}
			class:text-paper={activeFilter === ''}
			class:bg-rule={activeFilter !== ''}
			class:text-ink={activeFilter !== ''}
			onclick={() => (activeFilter = '')}
		>
			All
		</button>
		{#each ['family', 'romance', 'ally', 'enemy'] as kind}
			<button
				class="px-2.5 py-0.5 rounded-full text-xs font-medium transition-colors"
				class:bg-ink={activeFilter === kind}
				class:text-paper={activeFilter === kind}
				class:bg-rule={activeFilter !== kind}
				class:text-ink={activeFilter !== kind}
				onclick={() => (activeFilter = kind)}
			>
				{kind}
			</button>
		{/each}
	</div>

	<!-- Keyboard-accessible list view -->
	<div class="flex-1 overflow-auto">
		<ul class="space-y-2" aria-label="Relations list">
			{#each filteredRelations as rel (rel.id)}
				<li
					class="flex items-center gap-2 p-2 rounded-md border border-rule hover:border-rule-strong transition-colors"
				>
					<span
						class="inline-block w-3 h-0.5 rounded-full"
						style="background-color: {relationColors[rel.kind] ?? 'currentColor'}"
					></span>
					<span class="text-sm font-medium text-ink">{charName(rel.from_character_id)}</span>
					<span class="text-xs text-muted">{rel.label}</span>
					<span class="text-sm font-medium text-ink">{charName(rel.to_character_id)}</span>
					<span class="ml-auto text-xs text-muted capitalize">{rel.kind}</span>
				</li>
			{/each}

			{#if filteredRelations.length === 0}
				<li class="text-center py-8 text-sm text-muted">No relations match filter.</li>
			{/if}
		</ul>
	</div>
</div>
