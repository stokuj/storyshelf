<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		value: string;
		children: import('svelte').Snippet;
		[key: string]: any;
	}

	let { class: className = '', value, children, ...restProps }: Props = $props();
</script>

<button
	class={cn(
		'relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm text-ink outline-none transition-colors hover:bg-paper-2',
		className
	)}
	type="button"
	data-value={value}
	{...restProps}
>
	{@render children()}
</button>
