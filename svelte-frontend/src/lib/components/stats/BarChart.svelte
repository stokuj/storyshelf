<script lang="ts">
	interface Bar {
		label: string;
		value: number;
	}

	let { bars, ariaLabel = 'Bar chart' }: { bars: Bar[]; ariaLabel?: string } = $props();

	// Normalize bar heights to the tallest bar; floor at 1 to avoid /0.
	const max = $derived(Math.max(1, ...bars.map((b) => b.value)));
</script>

{#if bars.length === 0}
	<p class="text-sm text-muted">No data yet</p>
{:else}
	<div class="space-y-2" role="img" aria-label={ariaLabel}>
		<div class="flex items-end gap-2 h-40">
			{#each bars as bar (bar.label)}
				<div
					class="flex-1 rounded-t bg-accent min-h-[2px] transition-[height]"
					style="height: {(bar.value / max) * 100}%"
					title="{bar.label}: {bar.value}"
				></div>
			{/each}
		</div>
		<div class="flex gap-2">
			{#each bars as bar (bar.label)}
				<div class="flex-1 text-center">
					<div class="text-xs font-medium text-ink">{bar.value}</div>
					<div class="text-xs text-muted">{bar.label}</div>
				</div>
			{/each}
		</div>
	</div>
{/if}
