<script lang="ts">
	import { page } from '$app/stores';
	import { Button } from '$lib/components/ui/button';
	import { Search, AlertCircle } from 'lucide-svelte';
</script>

<div class="max-w-[1240px] mx-auto px-6 md:px-10 py-20 text-center">
	{#if $page.status === 404}
		<Search class="size-16 text-muted mx-auto mb-4" aria-hidden="true" />
		<h1 class="font-display text-4xl font-medium text-ink mb-2">Page not found</h1>
		<p class="text-muted mb-6 max-w-md mx-auto text-[15px] leading-relaxed">
			Like a book with a missing dust jacket — the words aren't where they should be.
		</p>
	{:else}
		<AlertCircle class="size-16 text-muted mx-auto mb-4" aria-hidden="true" />
		<h1 class="font-display text-4xl font-medium text-ink mb-2">Something's not right</h1>
		<p class="text-muted mb-6 max-w-md mx-auto">
			{$page.error?.message ?? 'An unexpected error occurred.'}
		</p>
	{/if}
	<div class="flex items-center justify-center gap-3">
		<Button variant="outline" href="/discover">Browse books</Button>
		<Button variant="ghost" href="/">Go home</Button>
	</div>
</div>
