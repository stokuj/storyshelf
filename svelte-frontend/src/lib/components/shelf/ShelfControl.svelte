<script lang="ts">
	import { BookPlus } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import { Button } from '$lib/components/ui/button';
	import StatusDropdown from './StatusDropdown.svelte';
	import { addToShelf, updateShelfEntry, deleteShelfEntry } from '$lib/api/shelf';
	import type { ShelfEntry, ShelfStatus } from '$lib/types/shelf';

	interface Props {
		bookSlug: string;
		initialEntry: ShelfEntry | null;
	}

	let { bookSlug, initialEntry }: Props = $props();
	let entry = $state<ShelfEntry | null>(initialEntry);
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
	<div class="flex items-center gap-2" data-testid="shelf-control">
		<div class="w-40"><StatusDropdown currentStatus={entry.status} onChange={changeStatus} /></div>
		<button
			type="button"
			class="text-xs text-muted hover:text-danger transition-colors"
			onclick={remove}
			disabled={busy}
		>
			Remove
		</button>
	</div>
{:else}
	<Button variant="outline" size="sm" onclick={add} disabled={busy} data-testid="add-to-shelf">
		<BookPlus class="mr-2 size-4" /> Add to shelf
	</Button>
{/if}
