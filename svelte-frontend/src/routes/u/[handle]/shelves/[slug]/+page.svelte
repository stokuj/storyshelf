<script lang="ts">
	import type { PageProps } from './$types';
	import BookCard from '$lib/components/book/BookCard.svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import { ArrowLeft, BookOpen } from 'lucide-svelte';
	import type { PublicShelfDetail } from '$lib/types/shelf';

	let { data }: PageProps = $props();
	let shelf: PublicShelfDetail = $derived(data.shelf);
</script>

<svelte:head>
	<title>{shelf.name} — Storyshelf</title>
</svelte:head>

<div class="max-w-[1240px] mx-auto px-6 md:px-10 py-8">
	<a
		href="/u/{data.handle}"
		class="inline-flex items-center gap-1 text-sm text-muted hover:text-ink transition-colors"
	>
		<ArrowLeft class="size-4" />
		@{data.handle}
	</a>

	<h1 class="font-display text-3xl font-medium text-ink mt-4">{shelf.name}</h1>
	{#if shelf.description}
		<p class="text-sm text-ink-2 mt-2 max-w-lg">{shelf.description}</p>
	{/if}
	<p class="text-sm text-muted mt-1">{shelf.book_count} books</p>

	{#if shelf.books.length > 0}
		<div
			class="mt-8 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6"
		>
			{#each shelf.books as book (book.slug)}
				<BookCard
					slug={book.slug}
					title={book.title}
					author={book.authors?.[0] ?? 'Unknown'}
					coverUrl={book.cover_url}
					genres={book.genres}
					avgRating={book.avg_rating}
				/>
			{/each}
		</div>
	{:else}
		<div class="mt-8">
			<EmptyState icon={BookOpen} title="Empty shelf" description="This shelf has no books yet." />
		</div>
	{/if}
</div>
