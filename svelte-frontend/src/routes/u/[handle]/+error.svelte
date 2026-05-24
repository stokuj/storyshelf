<script lang="ts">
	import { page } from '$app/stores';
	import { Button } from '$lib/components/ui/button';
	import { Lock, UserX } from 'lucide-svelte';
</script>

<div class="max-w-[1240px] mx-auto px-6 md:px-10 py-20 text-center">
	{#if $page.status === 404}
		<UserX class="size-16 text-muted mx-auto mb-4" aria-hidden="true" />
		<h1 class="font-display text-3xl font-medium text-ink mb-2">Profile not found</h1>
		<p class="text-muted mb-6">This user doesn't exist or their profile is private.</p>
	{:else}
		<Lock class="size-16 text-muted mx-auto mb-4" aria-hidden="true" />
		<h1 class="font-display text-3xl font-medium text-ink mb-2">Something went wrong</h1>
		<p class="text-muted mb-6">{$page.error?.message ?? 'An unexpected error occurred.'}</p>
	{/if}
	<Button variant="outline" href="/discover">Browse discover</Button>
</div>
