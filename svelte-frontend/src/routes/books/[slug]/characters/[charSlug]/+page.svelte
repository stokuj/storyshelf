<script lang="ts">
	import type { PageProps } from './$types';
	import RelationGraph from '$lib/components/character/RelationGraph.svelte';
	import { initials, monogramColor } from '$lib/utils/monogram';

	let { data }: PageProps = $props();
	let character = $derived(data.character);
</script>

<svelte:head>
	<title>{character.name} — Storyshelf</title>
</svelte:head>

<div class="mx-auto max-w-[900px] space-y-8 px-6 py-8 md:px-10">
	<a href="/books/{data.bookSlug}" class="text-sm text-info hover:underline">← Back to book</a>

	<div class="flex items-center gap-4">
		<div
			class="flex h-16 w-16 items-center justify-center rounded-full text-2xl font-bold text-white"
			style="background:{monogramColor(character.name)}"
		>
			{initials(character.name)}
		</div>
		<div>
			<h1 class="text-2xl font-bold">{character.name}</h1>
			{#if character.role}<p class="text-muted">{character.role}</p>{/if}
		</div>
	</div>

	{#if character.description}
		<p class="leading-relaxed">{character.description}</p>
	{/if}

	<section class="space-y-3">
		<h2 class="text-lg font-semibold">Relations</h2>
		<RelationGraph
			centerName={character.name}
			bookSlug={data.bookSlug}
			relations={character.relations}
		/>
	</section>
</div>
