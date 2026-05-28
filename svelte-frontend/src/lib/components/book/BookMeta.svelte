<script lang="ts">
	import type { Book } from '$lib/types';

	interface Props {
		book: Book;
	}
	let { book }: Props = $props();
</script>

<div class="text-sm text-muted">
	<div class="space-y-1.5">
		{#if book.year != null}
			<div class="flex gap-2">
				<span class="w-24 flex-shrink-0 text-ink-2">Published</span>
				<span class="text-ink">{book.year}</span>
			</div>
		{/if}
		{#if book.isbn}
			<div class="flex gap-2">
				<span class="w-24 flex-shrink-0 text-ink-2">ISBN</span>
				<span class="text-ink font-mono text-xs tracking-wide">{book.isbn}</span>
			</div>
		{/if}
		{#if book.page_count != null}
			<div class="flex gap-2">
				<span class="w-24 flex-shrink-0 text-ink-2">Pages</span>
				<span class="text-ink">{book.page_count}</span>
			</div>
		{/if}
		{#if book.serie}
			<div class="flex gap-2">
				<span class="w-24 flex-shrink-0 text-ink-2">Series</span>
				<span class="text-ink">
					{book.serie.name}
					{#if book.serie.position_in_series != null}
						<span class="text-muted"> #{book.serie.position_in_series}</span>
					{/if}
				</span>
			</div>
		{/if}
	</div>
</div>
