<script lang="ts">
	import type { Review } from '$lib/types/review';
	import RatingStars from '$lib/components/book/RatingStars.svelte';

	interface Props {
		review: Review;
	}
	let { review }: Props = $props();

	const date = $derived(new Date(review.created_at).toLocaleDateString());
</script>

<article data-testid="review-card" class="border-b border-rule py-4">
	<div class="flex items-center justify-between gap-2">
		<span class="font-medium">{review.author.display_name || `@${review.author.handle}`}</span>
		{#if review.author_rating}
			<RatingStars rating={review.author_rating} readonly size="sm" />
		{/if}
	</div>
	<p class="mt-2 whitespace-pre-wrap text-sm">{review.body}</p>
	<time class="mt-1 block text-xs text-muted">{date}</time>
</article>
