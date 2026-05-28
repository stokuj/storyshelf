<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Loader2 } from 'lucide-svelte';

	interface Props {
		loading: boolean;
		hasMore: boolean;
		onloadmore: () => void;
	}

	let { loading, hasMore, onloadmore }: Props = $props();
</script>

{#if loading}
	<div class="flex justify-center py-6">
		<Loader2 class="size-5 animate-spin text-muted" />
	</div>
{:else if hasMore}
	<div class="flex justify-center py-6">
		<Button variant="outline" size="sm" onclick={onloadmore}>Load more</Button>
	</div>
{/if}
