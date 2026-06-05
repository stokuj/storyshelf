<script lang="ts">
	import type { PageProps } from './$types';
	import type { FeedItem as FeedItemType } from '$lib/types/feed';
	import FeedItemComponent from '$lib/components/feed/FeedItem.svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import { Button } from '$lib/components/ui/button';
	import { fetchFeed } from '$lib/api/feed';
	import { Rss } from 'lucide-svelte';

	let { data }: PageProps = $props();

	// svelte-ignore state_referenced_locally
	let items = $state<FeedItemType[]>(data.items);
	// svelte-ignore state_referenced_locally
	let nextBefore = $state<string | null>(data.nextBefore);
	let loadingMore = $state(false);

	async function loadMore() {
		if (!nextBefore || loadingMore) return;
		loadingMore = true;
		const { data: res } = await fetchFeed(fetch, nextBefore);
		if (res) {
			items = [...items, ...res.results];
			nextBefore = res.next_before;
		}
		loadingMore = false;
	}
</script>

<svelte:head>
	<title>Feed — Storyshelf</title>
</svelte:head>

<div class="max-w-[700px] mx-auto px-6 md:px-10 py-8">
	<h1 class="font-display text-3xl font-medium text-ink mb-6">Feed</h1>

	{#if items.length === 0}
		<EmptyState
			icon={Rss}
			title="Nothing here yet"
			description="Follow some people to see their activity here."
			cta={{ label: 'Find people', href: '/users' }}
		/>
	{:else}
		<div>
			{#each items as item (item.type + item.actor.handle + item.book.slug + item.timestamp)}
				<FeedItemComponent {item} />
			{/each}
		</div>
		{#if nextBefore}
			<div class="flex justify-center mt-6">
				<Button variant="ghost" size="sm" onclick={loadMore} disabled={loadingMore}>
					{loadingMore ? 'Loading…' : 'Load more'}
				</Button>
			</div>
		{/if}
	{/if}
</div>
