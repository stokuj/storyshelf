<script lang="ts">
	import { page } from '$app/stores';
	import { Button } from '$lib/components/ui/button';
	import { BookOpen } from 'lucide-svelte';
</script>

<div class="max-w-[1240px] mx-auto px-6 md:px-10 py-20 text-center">
	<BookOpen class="size-16 text-muted mx-auto mb-4" aria-hidden="true" />
	<h1 class="font-display text-3xl font-medium text-ink mb-2">
		{#if $page.status === 404}
			Book not found
		{:else}
			Something went wrong
		{/if}
	</h1>
	<p class="text-muted mb-6 max-w-md mx-auto">
		{#if $page.status === 404}
			We couldn't find the book you're looking for. It may have been removed or the link may be
			incorrect.
		{:else}
			{$page.error?.message ?? 'An unexpected error occurred.'}
		{/if}
	</p>
	<div class="flex items-center justify-center gap-3">
		<Button variant="outline" href="/discover">Browse discover</Button>
		<Button variant="ghost" onclick={() => window.location.reload()}>Try again</Button>
	</div>
</div>
