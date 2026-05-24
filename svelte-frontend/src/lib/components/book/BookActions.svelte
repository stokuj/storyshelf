<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import {
		DropdownMenu,
		DropdownMenuContent,
		DropdownMenuItem,
		DropdownMenuTrigger,
		DropdownMenuSeparator
	} from '$lib/components/ui/dropdown-menu';
	import { BookOpen, Bookmark, Check, ChevronDown } from 'lucide-svelte';
	import { addToShelf, updateShelfEntry } from '$lib/api/shelves';
	import { toast } from 'svelte-sonner';

	interface Props {
		bookId: number;
		slug: string;
	}
	let { bookId }: Props = $props();

	let shelfStatus: 'none' | 'WANT_TO_READ' | 'READING' | 'READ' = $state('none');
	let loading = $state(false);

	async function setStatus(status: 'WANT_TO_READ' | 'READING' | 'READ') {
		loading = true;
		const prev = shelfStatus;
		shelfStatus = status;
		try {
			if (prev === 'none') {
				await addToShelf(fetch, bookId);
			} else {
				await updateShelfEntry(fetch, bookId, status);
			}
			toast.success(prev === 'none' ? 'Added to shelf' : 'Shelf updated');
		} catch {
			shelfStatus = prev;
			toast.error('Failed to update shelf');
		} finally {
			loading = false;
		}
	}

	const labels: Record<string, string> = {
		WANT_TO_READ: 'Want to read',
		READING: 'Currently reading',
		READ: 'Read'
	};
</script>

<div class="flex">
	<Button
		class="rounded-r-none flex-1"
		variant="outline"
		disabled={loading}
		onclick={() => setStatus(shelfStatus === 'none' ? 'WANT_TO_READ' : shelfStatus)}
	>
		<Bookmark class="mr-2 size-4" />
		{shelfStatus === 'none' ? 'Want to read' : labels[shelfStatus]}
	</Button>
	<DropdownMenu>
		<DropdownMenuTrigger
			class="rounded-l-none border-l-0 inline-flex items-center justify-center h-9 w-9 border border-rule bg-surface hover:bg-paper-2 text-ink shadow-sm rounded-r-md text-sm font-medium transition-colors"
			type="button"
		>
			<ChevronDown class="size-4" />
		</DropdownMenuTrigger>
		<DropdownMenuContent align="end">
			<DropdownMenuItem onclick={() => setStatus('WANT_TO_READ')}>
				<Bookmark class="mr-2 size-4" /> Want to read
			</DropdownMenuItem>
			<DropdownMenuItem onclick={() => setStatus('READING')}>
				<BookOpen class="mr-2 size-4" /> Currently reading
			</DropdownMenuItem>
			<DropdownMenuItem onclick={() => setStatus('READ')}>
				<Check class="mr-2 size-4" /> Read
			</DropdownMenuItem>
		</DropdownMenuContent>
	</DropdownMenu>
</div>
