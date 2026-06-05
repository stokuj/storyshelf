<script lang="ts">
	import ReviewCard from './ReviewCard.svelte';
	import LoadMore from '$lib/components/discover/LoadMore.svelte';
	import type { Review } from '$lib/types/review';

	interface Props {
		reviews: Review[];
		hasMore: boolean;
		loading: boolean;
		onloadmore: () => void;
		canLike?: boolean;
	}
	let { reviews, hasMore, loading, onloadmore, canLike = false }: Props = $props();
</script>

{#if reviews.length === 0}
	<p data-testid="reviews-empty" class="py-4 text-sm text-muted">No reviews yet.</p>
{:else}
	<div data-testid="review-list">
		{#each reviews as review (review.id)}
			<ReviewCard {review} {canLike} />
		{/each}
	</div>
	<LoadMore {loading} {hasMore} {onloadmore} />
{/if}
