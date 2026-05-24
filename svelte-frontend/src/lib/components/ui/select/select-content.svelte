<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		children: import('svelte').Snippet;
		[key: string]: any;
	}

	let { class: className = '', children, ...restProps }: Props = $props();
</script>

<div
	class={cn(
		'z-50 min-w-[8rem] overflow-hidden rounded-md border border-rule bg-surface p-1 shadow-md',
		className
	)}
	{...restProps}
>
	{@render children()}
</div>
