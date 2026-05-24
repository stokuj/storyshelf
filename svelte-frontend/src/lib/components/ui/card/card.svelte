<script lang="ts">
	import { cn } from '$lib/utils';
	interface Props {
		class?: string;
		children: import('svelte').Snippet;
		[key: string]: any;
	}
	let { class: className = '', children, ...restProps }: Props = $props();
</script>

<div class={cn('rounded-lg border border-rule bg-surface shadow-sm', className)} {...restProps}>
	{@render children()}
</div>
