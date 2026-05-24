<script lang="ts">
	import { cn } from '$lib/utils';
	interface Props {
		class?: string;
		children: import('svelte').Snippet;
		[key: string]: any;
	}
	let { class: className = '', children, ...restProps }: Props = $props();
</script>

<form class={cn('space-y-4', className)} {...restProps}>{@render children()}</form>
