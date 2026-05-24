<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		orientation?: 'horizontal' | 'vertical';
		[key: string]: any;
	}

	let { class: className = '', orientation = 'horizontal', ...restProps }: Props = $props();
</script>

{#if orientation === 'horizontal'}
	<hr class={cn('border-rule', className)} {...restProps} />
{:else}
	<div class={cn('border-l border-rule h-full', className)} {...restProps}></div>
{/if}
