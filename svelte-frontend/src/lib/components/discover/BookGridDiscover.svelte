<script lang="ts">
	import BookCard from '$lib/components/book/BookCard.svelte';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import type { Book } from '$lib/types/book';

	interface Props {
		books: Book[];
		loading?: boolean;
		skeletonCount?: number;
	}

	let { books, loading = false, skeletonCount = 6 }: Props = $props();
</script>

<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
	{#if loading && books.length === 0}
		{#each Array.from({ length: skeletonCount }, (_, i) => i) as i (i)}
			<div class="space-y-2">
				<Skeleton class="aspect-[2/3] w-full rounded-md" />
				<Skeleton class="h-4 w-3/4" />
				<Skeleton class="h-3 w-1/2" />
			</div>
		{/each}
	{:else}
		{#each books as book (book.id)}
			<BookCard
				slug={book.slug}
				title={book.title}
				author={book.authors?.[0] ?? 'Unknown'}
				coverUrl={book.cover_url}
				genres={book.genres}
				avgRating={book.avg_rating}
			/>
		{/each}
	{/if}
</div>
