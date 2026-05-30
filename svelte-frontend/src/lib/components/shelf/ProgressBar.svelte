<script lang="ts">
	interface Props {
		current: number | null;
		total: number | null;
	}

	let { current, total }: Props = $props();

	const percent = $derived(
		current != null && total != null && total > 0 ? Math.round((current / total) * 100) : null
	);
	const label = $derived(`${current ?? '?'} / ${total ?? '?'} pages`);
</script>

{#if current != null}
	<div
		class="w-full space-y-1"
		data-testid="progress-bar"
		data-current={current}
		data-total={total}
	>
		<div class="w-full bg-rule rounded-full h-1.5 overflow-hidden">
			<div
				class="bg-accent h-1.5 rounded-full transition-all duration-300"
				style="width:{percent ?? 0}%"
			></div>
		</div>
		<div class="flex items-center justify-between">
			<span class="text-xs text-muted">{label}</span>
			{#if percent != null}<span class="text-xs text-muted">{percent}%</span>{/if}
		</div>
	</div>
{/if}
