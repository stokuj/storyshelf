<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		children: import('svelte').Snippet;
		[key: string]: any;
	}

	let { children, ...restProps }: Props = $props();

	let open = $state(false);
</script>

<div class="relative inline-block text-left" {...restProps}>
	{@render children()}
</div>
