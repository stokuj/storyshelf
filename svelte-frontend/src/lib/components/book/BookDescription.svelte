<script lang="ts">
	interface Props {
		description: string | null;
	}
	let { description }: Props = $props();
</script>

{#if description}
	<div class="prose prose-stone max-w-none text-[15px] leading-relaxed text-ink">
		{#each description.split('\n\n') as paragraph}
			<p class="mb-3 last:mb-0">{paragraph}</p>
		{/each}
	</div>
{:else}
	<p class="text-sm text-muted italic">No description available.</p>
{/if}
