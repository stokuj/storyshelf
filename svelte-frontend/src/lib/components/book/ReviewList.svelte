<script lang="ts">
	import ReviewItem from './ReviewItem.svelte';
	import { MessageSquare } from 'lucide-svelte';

	interface Review {
		id: number;
		rating: number;
		content: string;
		createdAt: string;
		handle: string;
		bookTitle: string;
	}

	interface PaginatedReviews {
		data: Review[];
		page: number;
		per_page: number;
		total: number;
	}

	interface Props {
		reviews: PaginatedReviews;
	}
	let { reviews }: Props = $props();
</script>

{#if reviews.data.length === 0}
	<div class="text-center py-8 text-sm text-muted">
		<MessageSquare class="size-8 mx-auto mb-2 text-muted" aria-hidden="true" />
		<p>No reviews yet. Be the first to review!</p>
	</div>
{:else}
	<div class="space-y-4">
		{#each reviews.data as review (review.id)}
			<ReviewItem {review} />
		{/each}
	</div>
{/if}
