<script lang="ts">
	interface Props {
		children: import('svelte').Snippet;
		[key: string]: any;
	}

	let { children, ...restProps }: Props = $props();
</script>

<div class="relative inline-block text-left" {...restProps}>
	{@render children()}
</div>
