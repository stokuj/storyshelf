<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import type { Book } from '$lib/types';

	interface Props {
		book: Book;
	}
	let { book }: Props = $props();
</script>

<div class="space-y-2">
	<h1 class="font-display text-4xl md:text-5xl tracking-tight font-medium text-ink">
		{book.title}
	</h1>
	<p class="font-display italic text-ink-2">{book.author}</p>
	{#if book.publication_year || book.page_count}
		<div class="flex flex-wrap items-center gap-2 text-sm text-muted">
			{#if book.publication_year}
				<span>{book.publication_year}</span>
			{/if}
			{#if book.publication_year && book.page_count}
				<span aria-hidden="true">·</span>
			{/if}
			{#if book.page_count}
				<span>{book.page_count} pages</span>
			{/if}
		</div>
	{/if}
	{#if book.genres?.length}
		<div class="flex flex-wrap gap-1.5">
			{#each book.genres as genre}
				<Badge variant="secondary">{genre}</Badge>
			{/each}
		</div>
	{/if}
</div>
