<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		children: import('svelte').Snippet;
		[key: string]: any;
	}

	let { class: className = '', children, ...restProps }: Props = $props();
</script>

<button
	class={cn(
		'flex h-9 w-full items-center justify-between rounded-md border border-rule bg-surface px-3 py-1 text-sm text-ink shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent',
		className
	)}
	type="button"
	{...restProps}
>
	{@render children()}
</button>
