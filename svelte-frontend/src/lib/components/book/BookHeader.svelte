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
	{#if book.authors?.length}
		<p class="font-display italic text-ink-2">
			{#each book.authors as author, i (author)}
				<a
					href="/discover?author={encodeURIComponent(author)}"
					class="hover:text-accent transition-colors"
				>
					{author}
				</a>
				{#if i < book.authors.length - 1},
				{/if}
			{/each}
		</p>
	{/if}
	{#if book.genres?.length}
		<div class="flex flex-wrap gap-1.5">
			{#each book.genres as genre (genre)}
				<Badge variant="secondary">{genre}</Badge>
			{/each}
		</div>
	{/if}
</div>
