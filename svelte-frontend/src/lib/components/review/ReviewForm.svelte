<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { toast } from 'svelte-sonner';
	import { upsertReview, deleteReview } from '$lib/api/reviews';
	import type { Review } from '$lib/types/review';

	interface Props {
		bookSlug: string;
		myReview: Review | null;
		onsaved: (review: Review) => void;
		ondeleted: () => void;
	}
	let { bookSlug, myReview, onsaved, ondeleted }: Props = $props();

	let body = $state(myReview?.body ?? '');
	let saving = $state(false);

	async function save() {
		if (saving || body.trim() === '') return;
		saving = true;
		const { data, error } = await upsertReview(fetch, bookSlug, body.trim());
		if (error || !data) toast.error('Failed to save review');
		else {
			onsaved(data);
			toast.success(myReview ? 'Review updated' : 'Review posted');
		}
		saving = false;
	}

	async function remove() {
		if (saving || !myReview) return;
		saving = true;
		const { error } = await deleteReview(fetch, myReview.id);
		if (error) toast.error('Failed to delete review');
		else {
			body = '';
			ondeleted();
			toast.success('Review deleted');
		}
		saving = false;
	}
</script>

<div data-testid="review-form" class="flex flex-col gap-2">
	<textarea
		bind:value={body}
		data-testid="review-textarea"
		rows="4"
		placeholder="Write your review…"
		class="w-full rounded border border-rule bg-transparent p-2 text-sm"
	></textarea>
	<div class="flex gap-2">
		<Button size="sm" disabled={saving || body.trim() === ''} onclick={save}>
			{myReview ? 'Update' : 'Post'} review
		</Button>
		{#if myReview}
			<Button variant="outline" size="sm" disabled={saving} onclick={remove}>Delete</Button>
		{/if}
	</div>
</div>
