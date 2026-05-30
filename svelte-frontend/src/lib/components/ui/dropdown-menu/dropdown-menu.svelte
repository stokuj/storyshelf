<script lang="ts">
	import { setContext } from 'svelte';

	interface Props {
		children: import('svelte').Snippet;
		[key: string]: any;
	}

	let { children, ...restProps }: Props = $props();

	let open = $state(false);
	let rootEl: HTMLElement | undefined = $state();

	setContext('dropdown-menu', {
		get open() {
			return open;
		},
		toggle: () => (open = !open),
		close: () => (open = false)
	});

	function handleWindowClick(event: MouseEvent) {
		if (open && rootEl && !rootEl.contains(event.target as Node)) {
			open = false;
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (open && event.key === 'Escape') {
			open = false;
		}
	}
</script>

<svelte:window onclick={handleWindowClick} onkeydown={handleKeydown} />

<div bind:this={rootEl} class="relative inline-block text-left" {...restProps}>
	{@render children()}
</div>
