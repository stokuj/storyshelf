<script lang="ts">
	import { cn } from '$lib/utils';
	interface Props {
		class?: string;
		value?: string;
		children: import('svelte').Snippet;
		[key: string]: any;
	}
	let { class: className = '', value = '', children, ...restProps }: Props = $props();
</script>

<div class={cn('grid gap-2', className)} {...restProps}>{@render children()}</div>
