<script lang="ts">
	import type { PageProps } from './$types';
	import BookCover from '$lib/components/book/BookCover.svelte';
	import BookHeader from '$lib/components/book/BookHeader.svelte';
	import BookActions from '$lib/components/book/BookActions.svelte';
	import BookDescription from '$lib/components/book/BookDescription.svelte';
	import ReviewList from '$lib/components/book/ReviewList.svelte';
	import ReviewComposer from '$lib/components/book/ReviewComposer.svelte';
	import AICastPanel from '$lib/components/ai/AICastPanel.svelte';
	import { Badge } from '$lib/components/ui/badge';
	import { Separator } from '$lib/components/ui/separator';

	let { data }: PageProps = $props();
	let book = $derived(data.book!);
	let reviews = $derived(data.reviews);
	let extraction = $derived(data.extraction);
</script>

<svelte:head>
	<title>{book.title} — Storyshelf</title>
	<meta name="description" content={book.description?.slice(0, 160) ?? ''} />
	<meta property="og:title" content={book.title} />
	<meta property="og:image" content={book.cover_url ?? ''} />
</svelte:head>

<div class="max-w-[1240px] mx-auto px-6 md:px-10 py-8">
	<!-- Mobile: stacked layout -->
	<div class="lg:hidden space-y-6">
		<div class="flex gap-6">
			<BookCover coverUrl={book.cover_url} title={book.title} size="md" />
			<div class="flex-1">
				<BookHeader {book} />
				<div class="mt-3">
					<BookActions bookId={book.id} slug={book.slug} />
				</div>
				<div class="mt-2 text-sm text-muted">
					★ {book.avg_rating?.toFixed(1) ?? '—'} · {book.ratings_count} ratings
				</div>
			</div>
		</div>
		<BookDescription description={book.description} />
		<Separator />

		<!-- Mobile tab sections (no tab widget, just visual sections) -->
		<div class="space-y-6">
			<section>
				<h2 class="font-display text-xl font-medium text-ink mb-4">Reviews</h2>
				<ReviewComposer bookId={book.id} slug={book.slug} />
				<div class="mt-4">
					<ReviewList {reviews} />
				</div>
			</section>
			<Separator />
			<section>
				<h2 class="font-display text-xl font-medium text-ink mb-4">AI Cast</h2>
				<AICastPanel bookId={book.id} slug={book.slug} initialExtraction={extraction} />
			</section>
		</div>
	</div>

	<!-- Desktop: 3-column -->
	<div class="hidden lg:grid lg:grid-cols-[140px_1fr_260px] gap-8">
		<!-- Left: cover + actions -->
		<div class="space-y-4">
			<BookCover coverUrl={book.cover_url} title={book.title} size="md" />
			<BookActions bookId={book.id} slug={book.slug} />
			<div class="text-center text-sm text-muted">
				★ {book.avg_rating?.toFixed(1) ?? '—'} · {book.ratings_count} ratings
			</div>
		</div>

		<!-- Middle: info + reviews -->
		<div class="space-y-8 min-w-0">
			<BookHeader {book} />
			<BookDescription description={book.description} />
			<Separator />
			<div class="space-y-4">
				<h2 class="font-display text-2xl font-medium text-ink">Reviews</h2>
				<ReviewComposer bookId={book.id} slug={book.slug} />
				<ReviewList {reviews} />
			</div>
		</div>

		<!-- Right: AI panel -->
		<div class="sticky top-20 self-start">
			<AICastPanel bookId={book.id} slug={book.slug} initialExtraction={extraction} />
		</div>
	</div>
</div>
