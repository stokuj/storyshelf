<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		placeholder?: string;
		children?: import('svelte').Snippet;
		[key: string]: any;
	}

	let {
		class: className = '',
		placeholder = '',
		children = undefined,
		...restProps
	}: Props = $props();
</script>

<span class={cn(children !== undefined ? 'text-ink' : 'text-muted', className)} {...restProps}>
	{#if children !== undefined}
		{@render children()}
	{:else}
		{placeholder}
	{/if}
</span>
