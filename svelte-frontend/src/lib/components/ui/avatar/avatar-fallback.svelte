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
		'flex size-full items-center justify-center rounded-full bg-paper-2 text-xs font-medium text-muted',
		className
	)}
	{...restProps}
>
	{@render children()}
</div>
