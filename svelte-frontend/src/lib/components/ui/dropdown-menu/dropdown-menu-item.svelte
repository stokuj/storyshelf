<script lang="ts">
	import { getContext } from 'svelte';
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		disabled?: boolean;
		onclick?: (event: MouseEvent) => void;
		children: import('svelte').Snippet;
		[key: string]: any;
	}

	let {
		class: className = '',
		disabled = false,
		onclick,
		children,
		...restProps
	}: Props = $props();

	const menu = getContext('dropdown-menu') as { close: () => void };

	function handleClick(event: MouseEvent) {
		if (disabled) return;
		onclick?.(event);
		menu.close();
	}

	function handleKeydown(event: KeyboardEvent) {
		if (disabled) return;
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			handleClick(event as unknown as MouseEvent);
		}
	}
</script>

<!-- Rendered as a div (not a button) so consumers can nest a submit button (e.g. Sign out) without invalid nested buttons. -->
<div
	class={cn(
		'relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm text-ink outline-none transition-colors hover:bg-paper-2 focus:bg-paper-2',
		disabled && 'pointer-events-none opacity-50',
		className
	)}
	role="menuitem"
	tabindex={disabled ? -1 : 0}
	aria-disabled={disabled}
	onclick={handleClick}
	onkeydown={handleKeydown}
	{...restProps}
>
	{@render children()}
</div>
