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
		'fixed inset-y-0 right-0 z-50 flex w-full max-w-sm bg-surface border-l border-rule shadow-lg',
		className
	)}
	{...restProps}
>
	{@render children()}
</div>
