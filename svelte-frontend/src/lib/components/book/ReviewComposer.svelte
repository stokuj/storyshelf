<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import RatingStars from './RatingStars.svelte';
	import { createReview } from '$lib/api/books';
	import { reviewSchema } from '$lib/schemas/review';
	import { toast } from 'svelte-sonner';

	interface Props {
		bookId: number;
		slug: string;
	}
	let { bookId, slug }: Props = $props();

	let rating = $state(0);
	let content = $state('');
	let submitting = $state(false);
	let errorMessage = $state('');

	async function submit() {
		errorMessage = '';
		const result = reviewSchema.safeParse({ rating, content });
		if (!result.success) {
			errorMessage = result.error.errors[0]?.message ?? 'Validation error';
			return;
		}
		submitting = true;
		const { error } = await createReview(fetch, slug, { rating, content });
		submitting = false;
		if (error) {
			errorMessage = error.detail;
			return;
		}
		rating = 0;
		content = '';
		toast.success('Review posted!');
	}
</script>

<div class="p-4 rounded-md border border-rule bg-surface space-y-3">
	<h3 class="font-sans text-sm font-semibold text-ink">Write a review</h3>
	<div>
		<RatingStars bind:value={rating} size="md" />
	</div>
	<textarea
		class="w-full min-h-[80px] rounded-md border border-rule bg-paper px-3 py-2 text-sm text-ink placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent/40 resize-y"
		placeholder="What did you think of this book?"
		bind:value={content}
	></textarea>
	{#if errorMessage}
		<p class="text-xs text-danger">{errorMessage}</p>
	{/if}
	<div class="flex justify-end">
		<Button
			size="sm"
			disabled={submitting || rating === 0 || content.length < 10}
			onclick={submit}
		>
			{submitting ? 'Posting...' : 'Post review'}
		</Button>
	</div>
</div>
