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
	class={cn('relative flex size-10 shrink-0 overflow-hidden rounded-full', className)}
	{...restProps}
>
	{@render children()}
</div>
