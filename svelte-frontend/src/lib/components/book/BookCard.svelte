<script lang="ts">
	import BookCover from './BookCover.svelte';
	import { Badge } from '$lib/components/ui/badge';

	interface Props {
		id: number;
		slug: string;
		title: string;
		author: string;
		coverUrl: string | null;
		genres: string[];
		avgRating?: number;
	}
	let { id, slug, title, author, coverUrl, genres, avgRating }: Props = $props();
</script>

<a href="/books/{slug}" class="group block">
	<BookCover {coverUrl} {title} size="md" />
	<div class="mt-2 space-y-0.5">
		<h3
			class="font-sans text-sm font-semibold text-ink group-hover:text-accent transition-colors line-clamp-2"
		>
			{title}
		</h3>
		<p class="text-xs text-muted">{author}</p>
		{#if avgRating !== undefined}
			<p class="text-xs text-muted">★ {avgRating.toFixed(1)}</p>
		{/if}
		{#if genres.length > 0}
			<div class="flex flex-wrap gap-1 mt-1">
				{#each genres.slice(0, 3) as genre}
					<Badge variant="secondary" class="text-[10px] px-1.5 py-0">{genre}</Badge>
				{/each}
			</div>
		{/if}
	</div>
</a>
