<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		align?: 'start' | 'end';
		children: import('svelte').Snippet;
		[key: string]: any;
	}

	let { class: className = '', align = 'start', children, ...restProps }: Props = $props();
</script>

<div
	class={cn(
		'z-50 min-w-[8rem] overflow-hidden rounded-md border border-rule bg-surface p-1 shadow-md',
		align === 'end' ? 'right-0' : 'left-0',
		className
	)}
	{...restProps}
>
	{@render children()}
</div>
