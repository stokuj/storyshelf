<script lang="ts">
	import { BookPlus } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import { Button } from '$lib/components/ui/button';
	import StatusDropdown from './StatusDropdown.svelte';
	import ProgressBar from './ProgressBar.svelte';
	import { addToShelf, updateShelfEntry, deleteShelfEntry } from '$lib/api/shelf';
	import type { ShelfEntry, ShelfStatus } from '$lib/types/shelf';

	interface Props {
		bookSlug: string;
		initialEntry: ShelfEntry | null;
		bookPageCount?: number | null;
	}

	let { bookSlug, initialEntry, bookPageCount = null }: Props = $props();
	// Writable derived: locally mutable, resets when the parent swaps in a
	// different book (same-route navigation reuses this component, no remount).
	let entry = $derived(initialEntry);
	let busy = $state(false);

	async function add() {
		if (busy) return;
		busy = true;
		const { data, error } = await addToShelf(fetch, bookSlug, 'WANT_TO_READ');
		if (error || !data) toast.error('Failed to add to shelf');
		else entry = data;
		busy = false;
	}

	async function changeStatus(status: ShelfStatus) {
		if (!entry) return;
		const prev = entry.status;
		entry = { ...entry, status };
		const { error } = await updateShelfEntry(fetch, entry.id, { status });
		if (error) {
			entry = { ...entry, status: prev };
			toast.error('Failed to update status');
		}
	}

	async function changeProgress(currentPage: number) {
		if (!entry) return;
		const prev = entry.current_page;
		entry = { ...entry, current_page: currentPage };
		const { error } = await updateShelfEntry(fetch, entry.id, { current_page: currentPage });
		if (error) {
			entry = { ...entry, current_page: prev };
			toast.error('Failed to update progress');
		}
	}

	async function remove() {
		if (!entry || busy) return;
		busy = true;
		const { error } = await deleteShelfEntry(fetch, entry.id);
		if (error) toast.error('Failed to remove from shelf');
		else entry = null;
		busy = false;
	}
</script>

{#if entry}
	<div class="space-y-2" data-testid="shelf-control">
		<div class="flex items-center gap-2">
			<div class="w-40">
				<StatusDropdown currentStatus={entry.status} onChange={changeStatus} />
			</div>
			<button
				type="button"
				class="text-xs text-muted hover:text-danger transition-colors"
				onclick={remove}
				disabled={busy}
			>
				Remove
			</button>
		</div>
		{#if entry.status === 'READING'}
			<ProgressBar current={entry.current_page} total={bookPageCount} />
			<div class="flex items-center gap-2">
				<label class="text-xs text-muted" for="shelf-control-page">Page</label>
				<input
					id="shelf-control-page"
					type="number"
					min="0"
					max={bookPageCount ?? undefined}
					value={entry.current_page ?? 0}
					data-testid="current-page-input"
					class="w-20 rounded-md border border-rule bg-surface px-2 py-1 text-xs text-ink"
					onchange={(e) => changeProgress(Number(e.currentTarget.value))}
				/>
			</div>
		{/if}
	</div>
{:else}
	<Button variant="outline" size="sm" onclick={add} disabled={busy} data-testid="add-to-shelf">
		<BookPlus class="mr-2 size-4" /> Add to shelf
	</Button>
{/if}
