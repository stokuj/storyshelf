<script lang="ts">
	import { cn } from '$lib/utils';
	interface Props {
		class?: string;
		content: string;
		children: import('svelte').Snippet;
		[key: string]: any;
	}
	let { class: className = '', content, children, ...restProps }: Props = $props();
</script>

<div class={cn('relative group inline-flex', className)} {...restProps}>
	{@render children()}
	<div
		class="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 rounded bg-ink text-surface text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50"
	>
		{content}
	</div>
</div>
