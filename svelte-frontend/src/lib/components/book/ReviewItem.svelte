<script lang="ts">
	import CharacterAvatar from '$lib/components/character/CharacterAvatar.svelte';

	interface ReviewData {
		id: number;
		rating: number;
		content: string;
		createdAt: string;
		handle: string;
		bookTitle: string;
	}

	interface Props {
		review: ReviewData;
	}
	let { review }: Props = $props();
</script>

<div class="flex gap-3 p-3 rounded-md border border-rule bg-surface">
	<a href="/u/{review.handle}" class="shrink-0">
		<CharacterAvatar name={review.handle} size="sm" />
	</a>
	<div class="flex-1 min-w-0">
		<div class="flex items-center gap-2 mb-1">
			<a href="/u/{review.handle}" class="text-sm font-semibold text-ink hover:text-accent">
				@{review.handle}
			</a>
			<!-- Inline star rating display -->
			<span
				class="inline-flex items-center gap-0.5 text-accent text-xs"
				aria-label="{review.rating} out of 5 stars"
			>
				{'★'.repeat(review.rating)}{'☆'.repeat(5 - review.rating)}
			</span>
			<span class="text-xs text-muted">{new Date(review.createdAt).toLocaleDateString()}</span>
		</div>
		<p class="text-sm text-ink leading-relaxed">{review.content}</p>
	</div>
</div>
