<script lang="ts">
	import type { PageProps } from './$types';
	import BookCover from '$lib/components/book/BookCover.svelte';
	import BookHeader from '$lib/components/book/BookHeader.svelte';
	import BookMeta from '$lib/components/book/BookMeta.svelte';
	import BookDescription from '$lib/components/book/BookDescription.svelte';
	import { toast } from 'svelte-sonner';
	import RatingStars from '$lib/components/book/RatingStars.svelte';
	import ShelfControl from '$lib/components/shelf/ShelfControl.svelte';
	import ReviewSection from '$lib/components/review/ReviewSection.svelte';
	import { upsertRating, deleteRatingById } from '$lib/api/ratings';
	import { addBookToShelf, removeBookFromShelf } from '$lib/api/shelves';
	import type { Shelf } from '$lib/types/shelf';

	let { data }: PageProps = $props();
	let book = $derived(data.book!);

	// Writable derived: toggle reassigns via `.map(...)`, resets on navigation
	// to a different book (same-route navigation reuses this page component).
	let myShelves = $derived(data.myShelves);

	async function toggleShelf(shelf: Shelf) {
		const wasIn = shelf.contains_book === true;
		const { error } = await (wasIn
			? removeBookFromShelf(fetch, shelf.slug, data.book.slug)
			: addBookToShelf(fetch, shelf.slug, data.book.slug));
		if (error) {
			toast.error(wasIn ? 'Failed to remove from shelf' : 'Failed to add to shelf');
			return;
		}
		myShelves = myShelves.map((s) =>
			s.id === shelf.id
				? { ...s, contains_book: !wasIn, book_count: s.book_count + (wasIn ? -1 : 1) }
				: s
		);
	}

	// Writable derived: locally mutable, resets when navigating to a different
	// book (same-route navigation reuses this page component, no remount).
	let userRating = $derived(data.userRating?.rating ?? null);
	let ratingId = $derived(data.userRating?.id ?? null);
	let savingRating = $state(false);

	async function handleRate(star: number) {
		if (savingRating) return;
		savingRating = true;
		if (star === userRating && ratingId) {
			const { error } = await deleteRatingById(fetch, ratingId);
			if (error) toast.error('Failed to remove rating');
			else {
				userRating = null;
				ratingId = null;
			}
		} else {
			const { data: result, error } = await upsertRating(fetch, data.book.slug, star);
			if (error || !result) toast.error('Failed to save rating');
			else {
				userRating = result.rating;
				ratingId = result.id;
			}
		}
		savingRating = false;
	}
</script>

<svelte:head>
	<title>{book.title} — Storyshelf</title>
	<meta name="description" content={book.description?.slice(0, 160) ?? ''} />
	<meta property="og:title" content={book.title} />
	<meta property="og:image" content={book.cover_url ?? ''} />
</svelte:head>

<div class="max-w-[1240px] mx-auto px-6 md:px-10 py-8">
	<div class="flex flex-col gap-6 lg:grid lg:grid-cols-[140px_1fr] lg:gap-8 lg:items-start">
		<!-- Cover column (desktop) / cover + header row (mobile) -->
		<div class="flex gap-6 lg:block lg:space-y-4">
			<BookCover coverUrl={book.cover_url} title={book.title} size="md" />
			<!-- Mobile: header beside cover -->
			<div class="flex-1 lg:hidden">
				<BookHeader {book} />
				<div class="mt-2 text-sm text-muted">★ {book.avg_rating?.toFixed(1) ?? '—'}</div>
			</div>
			<!-- Desktop: avg under cover -->
			<div class="hidden lg:block text-center text-sm text-muted">
				★ {book.avg_rating?.toFixed(1) ?? '—'}
			</div>
		</div>

		<!-- Main content column (reflows below cover row on mobile) -->
		<div class="space-y-6 lg:space-y-8 min-w-0">
			<!-- Desktop: header in content column -->
			<div class="hidden lg:block">
				<BookHeader {book} />
			</div>

			<!-- Rating + shelf controls — rendered exactly once -->
			<div class="flex flex-col gap-3">
				<div class="flex items-center gap-2">
					<RatingStars
						rating={userRating}
						onRate={data.user ? handleRate : undefined}
						readonly={!data.user}
					/>
					{#if data.book.ratings_count > 0}
						<span class="text-sm text-muted"
							>{data.book.avg_rating.toFixed(1)} ({data.book.ratings_count})</span
						>
					{/if}
				</div>
				{#if data.user}
					<ShelfControl bookSlug={data.book.slug} initialEntry={data.shelfEntry} />
					<details class="relative w-fit" data-testid="add-to-shelf-dropdown">
						<summary
							class="flex items-center gap-1.5 w-fit cursor-pointer list-none rounded-md border border-rule bg-surface px-2.5 py-1.5 text-xs font-medium transition-colors hover:bg-paper-2"
						>
							Add to shelf
						</summary>
						<ul
							class="absolute top-full left-0 mt-1 z-20 min-w-48 rounded-md border border-rule bg-surface shadow-lg py-1"
						>
							{#each myShelves as shelf (shelf.id)}
								<li>
									<label
										class="flex items-center gap-2 px-2.5 py-1.5 text-xs cursor-pointer hover:bg-paper-2"
									>
										<input
											type="checkbox"
											checked={shelf.contains_book === true}
											onclick={() => toggleShelf(shelf)}
										/>
										<span class="flex-1">{shelf.name}</span>
										<span class="text-muted">{shelf.book_count}</span>
									</label>
								</li>
							{/each}
							{#if myShelves.length === 0}
								<li class="px-2.5 py-1.5 text-xs">
									<a href="/shelf" class="text-info hover:underline">Create your first shelf</a>
								</li>
							{/if}
						</ul>
					</details>
				{/if}
			</div>

			<!-- BookMeta: desktop only (mobile intentionally omits it, as before) -->
			<div class="hidden lg:block">
				<BookMeta {book} />
			</div>

			<BookDescription description={book.description} />

			<ReviewSection
				bookSlug={data.book.slug}
				initialReviews={data.reviews}
				initialTotal={data.reviewsTotal}
				myReview={data.myReview}
				isAuthenticated={!!data.user}
			/>
		</div>
	</div>
</div>
