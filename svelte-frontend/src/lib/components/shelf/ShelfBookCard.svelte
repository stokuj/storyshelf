<script lang="ts">
	import { goto } from '$app/navigation';
	import { Trash2 } from 'lucide-svelte';
	import BookCover from '$lib/components/book/BookCover.svelte';
	import RatingStars from '$lib/components/book/RatingStars.svelte';
	import ProgressBar from './ProgressBar.svelte';
	import StatusDropdown from './StatusDropdown.svelte';
	import { Badge } from '$lib/components/ui/badge';
	import type { ShelfEntryWithRating, ShelfStatus } from '$lib/types/shelf';

	interface Props {
		entry: ShelfEntryWithRating;
		onDelete: (id: number) => void;
		onRate: (bookSlug: string, rating: number, entryId: number) => Promise<void>;
		onStatusChange: (entryId: number, status: ShelfStatus) => Promise<void>;
		onProgressChange: (entryId: number, currentPage: number) => Promise<void>;
	}

	let { entry, onDelete, onRate, onStatusChange, onProgressChange }: Props = $props();

	const book = $derived(entry.book);
	const authors = $derived(book.authors.join(', '));
	const statusLabels: Record<ShelfStatus, string> = {
		WANT_TO_READ: 'Want to Read',
		READING: 'Reading',
		READ: 'Read'
	};

	let confirming = $state(false);

	function navigate() {
		goto(`/books/${book.slug}`);
	}
</script>

<div
	class="flex gap-4 rounded-lg border border-rule bg-surface p-4 shadow-sm hover:shadow-md transition-shadow"
	data-testid="shelf-book-card"
	data-status={entry.status}
	data-book-slug={book.slug}
>
	<button
		type="button"
		class="flex-shrink-0 cursor-pointer"
		onclick={navigate}
		aria-label="Go to book detail"
	>
		<BookCover coverUrl={book.cover_url} title={book.title} size="sm" />
	</button>

	<div class="flex-1 min-w-0 space-y-2">
		<div class="space-y-0.5">
			<button
				type="button"
				class="text-left hover:text-accent transition-colors"
				onclick={navigate}
			>
				<h3 class="font-sans text-sm font-semibold text-ink line-clamp-1">{book.title}</h3>
			</button>
			<p class="text-xs text-muted">{authors}</p>
			<div class="flex flex-wrap items-center gap-2 pt-0.5">
				<Badge variant="outline" class="text-[10px] px-1.5 py-0">{statusLabels[entry.status]}</Badge
				>
				{#if book.avg_rating > 0}
					<span class="text-[10px] text-muted">★ {book.avg_rating.toFixed(1)}</span>
				{/if}
			</div>
		</div>

		<div class="pt-1">
			<RatingStars
				rating={entry.user_rating}
				onRate={(r) => onRate(book.slug, r, entry.id)}
				size="sm"
			/>
		</div>

		{#if entry.status === 'READING'}
			<ProgressBar current={entry.current_page} total={book.page_count} />
			<div class="flex items-center gap-2 pt-1">
				<label class="text-xs text-muted" for="page-{entry.id}">Page</label>
				<input
					id="page-{entry.id}"
					type="number"
					min="0"
					max={book.page_count ?? undefined}
					value={entry.current_page ?? 0}
					data-testid="current-page-input"
					class="w-20 rounded-md border border-rule bg-surface px-2 py-1 text-xs text-ink"
					onchange={(e) => onProgressChange(entry.id, Number(e.currentTarget.value))}
				/>
			</div>
		{/if}

		<div class="flex items-center justify-between gap-2 pt-1">
			<div class="w-36">
				<StatusDropdown
					currentStatus={entry.status}
					onChange={(s) => onStatusChange(entry.id, s)}
				/>
			</div>
			{#if confirming}
				<div class="flex items-center gap-1">
					<button
						type="button"
						data-testid="shelf-delete-confirm"
						class="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-danger bg-danger/10 hover:bg-danger/20 transition-colors"
						onclick={() => {
							confirming = false;
							onDelete(entry.id);
						}}
					>
						<Trash2 class="size-3" /><span>Confirm remove?</span>
					</button>
					<button
						type="button"
						class="rounded-md px-2 py-1 text-xs text-muted hover:text-ink"
						onclick={() => (confirming = false)}
					>
						Cancel
					</button>
				</div>
			{:else}
				<button
					type="button"
					data-testid="shelf-delete-btn"
					class="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted hover:text-danger hover:bg-danger/5 transition-colors"
					onclick={() => (confirming = true)}
				>
					<Trash2 class="size-3" /><span>Remove</span>
				</button>
			{/if}
		</div>
	</div>
</div>
