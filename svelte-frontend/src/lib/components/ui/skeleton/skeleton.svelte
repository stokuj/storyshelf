<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		[key: string]: any;
	}

	let { class: className = '', ...restProps }: Props = $props();
</script>

<div class={cn('animate-pulse rounded-md bg-paper-2', className)} {...restProps}></div>
