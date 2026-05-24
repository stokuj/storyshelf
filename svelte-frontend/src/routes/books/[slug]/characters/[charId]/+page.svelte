<script lang="ts">
	import type { PageProps } from './$types';
	import CharacterAvatar from '$lib/components/character/CharacterAvatar.svelte';
	import RelationBadge from '$lib/components/character/RelationBadge.svelte';
	import AIBadge from '$lib/components/ai/AIBadge.svelte';
	import { ArrowLeft } from 'lucide-svelte';
	import type { Relation } from '$lib/types';

	let { data }: PageProps = $props();
	let book = $derived(data.book!);
	let character = $derived(data.character!);
	let allRelations: Relation[] = $derived(data.relations ?? []);

	let characterRelations = $derived(
		allRelations.filter(
			(r) => r.from_character_id === character.id || r.to_character_id === character.id
		)
	);

	function relatedCharName(rel: Relation): string {
		if (rel.from_character_id === character.id) {
			return `Character #${rel.to_character_id}`;
		}
		return `Character #${rel.from_character_id}`;
	}
</script>

<svelte:head>
	<title>{character.name} in {book.title} — Storyshelf</title>
</svelte:head>

<div class="max-w-[1240px] mx-auto px-6 md:px-10 py-8">
	<a
		href="/books/{book.slug}"
		class="inline-flex items-center gap-1 text-sm text-muted hover:text-accent mb-4"
	>
		<ArrowLeft class="size-3.5" /> Back to {book.title}
	</a>

	<div class="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-8">
		<!-- Left: bio + quotes -->
		<div class="space-y-6">
			<div class="flex items-start gap-5">
				<CharacterAvatar name={character.name} size="xl" />
				<div class="flex-1">
					<div class="flex items-center gap-2">
						<h1 class="font-display text-3xl font-medium text-ink">{character.name}</h1>
						{#if character.source !== 'ai-verified' && character.source !== 'human'}
							<AIBadge />
						{/if}
					</div>
					{#if character.also_known_as?.length}
						<p class="text-sm text-muted mt-0.5">AKA: {character.also_known_as.join(', ')}</p>
					{/if}
					<div class="flex items-center gap-2 mt-2">
						<span
							class="inline-flex items-center rounded-full border border-rule px-2.5 py-0.5 text-xs font-semibold capitalize"
						>
							{character.role}
						</span>
						{#if character.archetype}
							<span
								class="inline-flex items-center rounded-full border border-transparent bg-paper-2 px-2.5 py-0.5 text-xs font-semibold text-ink-2 capitalize"
							>
								{character.archetype}
							</span>
						{/if}
					</div>
				</div>
			</div>

			<hr class="border-rule" />

			{#if character.short_bio || character.long_bio}
				<div class="space-y-3">
					<h2 class="font-display text-xl font-medium text-ink">Bio</h2>
					{#if character.short_bio}
						<p class="text-[15px] leading-relaxed text-ink">{character.short_bio}</p>
					{/if}
					{#if character.long_bio}
						<p class="text-[15px] leading-relaxed text-ink-2">{character.long_bio}</p>
					{/if}
				</div>
			{/if}

			{#if character.tags?.length}
				<div class="space-y-2">
					<h2 class="font-display text-xl font-medium text-ink">Tags</h2>
					<div class="flex flex-wrap gap-1.5">
						{#each character.tags as tag}
							<span
								class="inline-flex items-center rounded-full border border-transparent bg-paper-2 px-2.5 py-0.5 text-xs font-semibold text-ink-2"
							>
								{tag}
							</span>
						{/each}
					</div>
				</div>
			{/if}
		</div>

		<!-- Right: relations -->
		<div class="space-y-4">
			<h2 class="font-display text-xl font-medium text-ink">Relations</h2>
			{#if characterRelations.length > 0}
				<div class="space-y-2">
					{#each characterRelations as rel (rel.id)}
						<div class="p-3 rounded-md border border-rule bg-surface space-y-1">
							<RelationBadge kind={rel.kind} label={rel.label} />
							<p class="text-xs text-muted">
								with {relatedCharName(rel)}
							</p>
							{#if rel.spoiler_chapter}
								<span class="block text-xs text-muted"
									>Spoiler: chapter {rel.spoiler_chapter}</span
								>
							{/if}
						</div>
					{/each}
				</div>
			{:else}
				<p class="text-sm text-muted">No known relations.</p>
			{/if}
		</div>
	</div>
</div>
