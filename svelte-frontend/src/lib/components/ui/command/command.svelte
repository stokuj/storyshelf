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
		'flex h-full w-full flex-col overflow-hidden rounded-md border border-rule bg-surface',
		className
	)}
	{...restProps}
>
	{@render children()}
</div>
