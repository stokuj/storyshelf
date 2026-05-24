<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		value?: string;
		placeholder?: string;
		type?: string;
		[key: string]: any;
	}

	let {
		class: className = '',
		value = $bindable(''),
		placeholder = '',
		type = 'text',
		...restProps
	}: Props = $props();
</script>

<input
	{type}
	{placeholder}
	{value}
	class={cn(
		'flex h-9 w-full rounded-md border border-rule bg-surface px-3 py-1 text-sm text-ink shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-ink placeholder:text-muted focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent disabled:cursor-not-allowed disabled:opacity-50',
		className
	)}
	{...restProps}
/>
