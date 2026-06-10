<script lang="ts">
	import { getContext } from 'svelte';
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		align?: 'start' | 'end';
		children: import('svelte').Snippet;
		[key: string]: any;
	}

	let { class: className = '', align = 'start', children, ...restProps }: Props = $props();

	const menu = getContext('dropdown-menu') as { open: boolean };
</script>

{#if menu.open}
	<div
		class={cn(
			'absolute z-50 mt-2 min-w-[8rem] overflow-hidden rounded-md border border-rule bg-surface p-1 shadow-md',
			align === 'end' ? 'right-0' : 'left-0',
			className
		)}
		role="menu"
		{...restProps}
	>
		{@render children()}
	</div>
{/if}
