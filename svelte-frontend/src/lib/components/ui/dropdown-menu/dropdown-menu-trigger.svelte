<script lang="ts">
	import { getContext } from 'svelte';
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		children: import('svelte').Snippet;
		[key: string]: any;
	}

	let { class: className = '', children, ...restProps }: Props = $props();

	const menu = getContext('dropdown-menu') as { open: boolean; toggle: () => void };

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			menu.toggle();
		}
	}
</script>

<!-- Wrapper is a div (not a button) so consumers can place an inner button (e.g. avatar) without invalid nested buttons. -->
<div
	class={cn('inline-flex items-center justify-center', className)}
	role="button"
	tabindex="0"
	aria-haspopup="menu"
	aria-expanded={menu.open}
	onclick={() => menu.toggle()}
	onkeydown={handleKeydown}
	{...restProps}
>
	{@render children()}
</div>
