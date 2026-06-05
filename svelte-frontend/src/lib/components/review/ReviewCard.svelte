<script lang="ts">
	import type { Review } from '$lib/types/review';
	import RatingStars from '$lib/components/book/RatingStars.svelte';
	import { Heart } from 'lucide-svelte';
	import { likeReview, unlikeReview } from '$lib/api/reviews';

	interface Props {
		review: Review;
		canLike?: boolean;
	}
	let { review, canLike = false }: Props = $props();

	const date = $derived(new Date(review.created_at).toLocaleDateString());

	// svelte-ignore state_referenced_locally
	let liked = $state(review.is_liked);
	// svelte-ignore state_referenced_locally
	let count = $state(review.likes_count);
	let pending = $state(false);

	async function toggleLike() {
		if (pending) return;
		pending = true;
		// Optimistic update
		const wasLiked = liked;
		const prevCount = count;
		liked = !wasLiked;
		count = wasLiked ? count - 1 : count + 1;

		const { data, error } = wasLiked
			? await unlikeReview(fetch, review.id)
			: await likeReview(fetch, review.id);

		if (error || !data) {
			// Revert on error
			liked = wasLiked;
			count = prevCount;
		} else {
			liked = data.is_liked;
			count = data.likes_count;
		}
		pending = false;
	}
</script>

<article data-testid="review-card" class="border-b border-rule py-4">
	<div class="flex items-center justify-between gap-2">
		<a href="/u/{review.author.handle}" class="font-medium hover:text-accent transition-colors">
			{review.author.display_name || `@${review.author.handle}`}
		</a>
		{#if review.author_rating}
			<RatingStars rating={review.author_rating} readonly size="sm" />
		{/if}
	</div>
	<p class="mt-2 whitespace-pre-wrap text-sm">{review.body}</p>
	<div class="mt-1 flex items-center gap-3">
		<time class="text-xs text-muted">{date}</time>
		<div class="flex items-center gap-1">
			{#if canLike}
				<button
					data-testid="like-button"
					onclick={toggleLike}
					disabled={pending}
					class="flex items-center gap-1 text-xs text-muted hover:text-accent transition-colors disabled:opacity-50"
					aria-label={liked ? 'Unlike review' : 'Like review'}
				>
					<Heart class="size-3.5 {liked ? 'fill-accent text-accent' : ''}" />
				</button>
			{:else}
				<Heart class="size-3.5 text-muted {liked ? 'fill-accent text-accent' : ''}" />
			{/if}
			<span data-testid="like-count" class="text-xs text-muted">{count}</span>
		</div>
	</div>
</article>
