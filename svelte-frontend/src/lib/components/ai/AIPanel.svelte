<script lang="ts">
	interface Props {
		title: string;
		children: import('svelte').Snippet;
	}
	let { title, children }: Props = $props();
</script>

<div class="bg-accent-soft border border-dashed border-accent/40 rounded-lg p-4">
	<h3 class="font-display text-lg font-medium text-accent-ink mb-3 flex items-center gap-2">
		<svg
			class="size-4 text-accent"
			xmlns="http://www.w3.org/2000/svg"
			width="16"
			height="16"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			stroke-width="1.75"
			stroke-linecap="round"
			stroke-linejoin="round"
			><path
				d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"
			/></svg
		>
		{title}
	</h3>
	<div class="space-y-3">
		{@render children()}
	</div>
</div>
