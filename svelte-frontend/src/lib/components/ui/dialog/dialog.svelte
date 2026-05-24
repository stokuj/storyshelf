<script lang="ts">
	import { cn } from '$lib/utils';
	interface Props {
		class?: string;
		children: import('svelte').Snippet;
		[key: string]: any;
	}
	let { class: className = '', children, ...restProps }: Props = $props();
</script>

<div class={cn('fixed inset-0 z-50 flex items-center justify-center', className)} {...restProps}>
	<div class="fixed inset-0 bg-ink/50"></div>
	<div
		class="relative z-50 rounded-lg border border-rule bg-surface p-6 shadow-lg max-w-lg w-full mx-4"
	>
		{@render children()}
	</div>
</div>
