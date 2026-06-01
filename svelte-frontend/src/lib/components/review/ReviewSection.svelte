<script lang="ts">
	import ReviewForm from './ReviewForm.svelte';
	import ReviewList from './ReviewList.svelte';
	import { fetchReviews } from '$lib/api/reviews';
	import { toast } from 'svelte-sonner';
	import type { Review } from '$lib/types/review';

	interface Props {
		bookSlug: string;
		initialReviews: Review[];
		initialTotal: number;
		myReview: Review | null;
		isAuthenticated: boolean;
	}
	let { bookSlug, initialReviews, initialTotal, myReview, isAuthenticated }: Props = $props();

	let reviews = $state<Review[]>(initialReviews);
	let total = $state(initialTotal);
	let currentPage = $state(1);
	let loadingMore = $state(false);
	let mine = $state<Review | null>(myReview);

	let hasMore = $derived(reviews.length < total);

	function onSaved(review: Review) {
		mine = review;
		const idx = reviews.findIndex((r) => r.id === review.id);
		if (idx >= 0) reviews[idx] = review;
		else {
			reviews = [review, ...reviews];
			total += 1;
		}
	}

	function onDeleted() {
		if (mine) {
			reviews = reviews.filter((r) => r.id !== mine!.id);
			total -= 1;
		}
		mine = null;
	}

	async function loadMore() {
		loadingMore = true;
		const { data, error } = await fetchReviews(fetch, bookSlug, currentPage + 1);
		if (error || !data) {
			toast.error('Failed to load more reviews');
		} else {
			// Skip any review already present (e.g. the user's own pinned review).
			const seen = new Set(reviews.map((r) => r.id));
			reviews = [...reviews, ...data.data.filter((r) => !seen.has(r.id))];
			currentPage = data.page;
			total = data.total;
		}
		loadingMore = false;
	}
</script>

<section class="space-y-4">
	<h2 class="text-lg font-semibold">Reviews</h2>
	{#if isAuthenticated}
		<ReviewForm {bookSlug} myReview={mine} onsaved={onSaved} ondeleted={onDeleted} />
	{/if}
	<ReviewList {reviews} {hasMore} loading={loadingMore} onloadmore={loadMore} />
</section>
