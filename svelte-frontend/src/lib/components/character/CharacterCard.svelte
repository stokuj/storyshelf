<script lang="ts">
	import type { CharacterSummary } from '$lib/types/character';
	import { initials, monogramColor } from '$lib/utils/monogram';

	let { character, bookSlug }: { character: CharacterSummary; bookSlug: string } = $props();
</script>

<a
	href="/books/{bookSlug}/characters/{character.slug}"
	class="flex flex-col items-center gap-2 rounded-xl border border-rule bg-surface p-4 text-center transition-colors hover:bg-paper-2"
>
	<div
		class="flex h-14 w-14 items-center justify-center rounded-full text-lg font-bold text-white"
		style="background:{monogramColor(character.name)}"
	>
		{initials(character.name)}
	</div>
	<div class="text-sm font-semibold leading-tight">{character.name}</div>
	{#if character.role}
		<div class="text-xs text-muted">{character.role}</div>
	{/if}
</a>
