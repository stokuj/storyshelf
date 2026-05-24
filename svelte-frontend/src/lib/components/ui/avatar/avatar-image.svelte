<script lang="ts">
	interface Props {
		src?: string;
		alt?: string;
		class?: string;
		[key: string]: any;
	}

	let { src = '', alt = '', class: className = '', ...restProps }: Props = $props();
</script>

{#if src}
	<img {src} {alt} class="absolute inset-0 size-full object-cover {className}" {...restProps} />
{/if}
