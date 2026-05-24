<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		children: import('svelte').Snippet;
		[key: string]: any;
	}

	let { class: className = '', children, ...restProps }: Props = $props();
</script>

<button
	class={cn('inline-flex items-center justify-center', className)}
	type="button"
	{...restProps}
>
	{@render children()}
</button>
