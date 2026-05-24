<script lang="ts">
	import { cn } from '$lib/utils';
	interface Props {
		class?: string;
		forAttr?: string;
		children: import('svelte').Snippet;
		[key: string]: any;
	}
	let { class: className = '', forAttr = '', children, ...restProps }: Props = $props();
</script>

<label
	for={forAttr}
	class={cn(
		'text-sm font-medium text-ink leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70',
		className
	)}
	{...restProps}>{@render children()}</label
>
