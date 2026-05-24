<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import type { ComponentType } from 'svelte';
	interface Props {
		icon: ComponentType;
		title: string;
		description: string;
		cta?: { label: string; href: string };
	}
	let { icon: Icon, title, description, cta }: Props = $props();
</script>

<div class="flex flex-col items-center justify-center py-16 text-center">
	<Icon class="size-12 text-muted mb-4" aria-hidden="true" />
	<h3 class="font-display text-xl font-medium text-ink mb-1">{title}</h3>
	<p class="text-sm text-muted max-w-sm mb-4">{description}</p>
	{#if cta}
		<Button variant="outline" size="sm" href={cta.href}>{cta.label}</Button>
	{/if}
</div>
