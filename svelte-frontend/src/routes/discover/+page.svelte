<script lang="ts">
	import type { PageProps } from './$types';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { Book, SearchX } from 'lucide-svelte';
	import BookGrid from '$lib/components/book/BookGrid.svelte';
	import BookGridSkeleton from '$lib/components/book/BookGridSkeleton.svelte';
	import FilterBar from '$lib/components/discover/FilterBar.svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import { Button } from '$lib/components/ui/button';

	let { data }: PageProps = $props();
	let books = $derived(data.books?.data ?? []);
	let total = $derived(data.books?.total ?? 0);
	let currentPage = $derived(Number($page.url.searchParams.get('page') ?? 1));

	function loadMore() {
		const next = currentPage + 1;
		const url = new URL($page.url);
		url.searchParams.set('page', String(next));
		goto(url, { keepFocus: true });
	}
</script>

<svelte:head>
	<title>Discover Books — Storyshelf</title>
	<meta name="description" content="Discover and track your favorite books on Storyshelf." />
</svelte:head>

<div class="max-w-[1240px] mx-auto px-6 md:px-10 py-8">
	<div class="mb-8">
		<h1 class="font-display text-4xl md:text-5xl tracking-tight font-medium text-ink mb-2">
			Discover
		</h1>
		<p class="text-ink-2 text-[15px] leading-relaxed">
			Browse books, find your next read, and explore AI-extracted characters.
		</p>
	</div>

	<FilterBar />

	{#if books.length === 0}
		<EmptyState
			icon={SearchX}
			title="No books found"
			description="Try adjusting your filters or search query."
		/>
	{:else}
		<BookGrid
			books={books.map((b) => ({
				id: b.id,
				slug: b.slug,
				title: b.title,
				author: b.author,
				coverUrl: b.cover_url,
				genres: b.genres,
				avgRating: b.avg_rating
			}))}
		/>

		{#if books.length < total}
			<div class="mt-8 text-center">
				<Button variant="outline" onclick={loadMore}>
					Load more ({total - books.length} remaining)
				</Button>
			</div>
		{/if}
	{/if}
</div>
