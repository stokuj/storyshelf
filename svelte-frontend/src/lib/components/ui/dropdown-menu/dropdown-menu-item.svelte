<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		disabled?: boolean;
		children: import('svelte').Snippet;
		[key: string]: any;
	}

	let { class: className = '', disabled = false, children, ...restProps }: Props = $props();
</script>

<button
	class={cn(
		'relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm text-ink outline-none transition-colors hover:bg-paper-2 focus:bg-paper-2',
		disabled && 'pointer-events-none opacity-50',
		className
	)}
	{disabled}
	type="button"
	{...restProps}
>
	{@render children()}
</button>
