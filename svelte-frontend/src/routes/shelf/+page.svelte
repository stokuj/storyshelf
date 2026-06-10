<script lang="ts">
	import { page } from '$app/state';
	import { goto, invalidateAll } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { BookOpen, Library, BookMarked } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import ShelfBookCard from '$lib/components/shelf/ShelfBookCard.svelte';
	import { upsertRating, deleteRatingById } from '$lib/api/ratings';
	import { updateShelfEntry, deleteShelfEntry } from '$lib/api/shelf';
	import { createShelf } from '$lib/api/shelves';
	import type { ShelfStatus, Shelf } from '$lib/types/shelf';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	let viewTab = $state<'status' | 'shelves'>('status');

	// Mirrors loader data (re-fetched via invalidateAll() after create). Never mutated
	// in place — only reassigned — so a writable $derived is safe (no in-place gotcha).
	let shelves = $derived<Shelf[]>(data.shelves);

	let newName = $state('');
	let newPublic = $state(false);
	let creating = $state(false);
	let createError = $state('');

	async function handleCreate() {
		if (!newName.trim()) return;
		creating = true;
		createError = '';
		const { error } = await createShelf(fetch, { name: newName.trim(), is_public: newPublic });
		creating = false;
		if (error) {
			createError = error.detail;
			return;
		}
		newName = '';
		newPublic = false;
		await invalidateAll();
	}

	// Deep-reactive local copy: handlers mutate entries in place (entries[i] = …),
	// which needs a $state proxy — a writable $derived would mutate the raw loader
	// array without triggering reactivity. Intentional one-time snapshot.
	// svelte-ignore state_referenced_locally
	let entries = $state(data.entries);
	let activeTab = $state<ShelfStatus>('WANT_TO_READ');

	const tabs: { id: ShelfStatus; label: string; icon: typeof BookOpen }[] = [
		{ id: 'WANT_TO_READ', label: 'Want to Read', icon: BookOpen },
		{ id: 'READING', label: 'Reading', icon: Library },
		{ id: 'READ', label: 'Read', icon: BookMarked }
	];

	const emptyMessages: Record<
		ShelfStatus,
		{ title: string; description: string; cta?: { label: string; href: string } }
	> = {
		WANT_TO_READ: {
			title: 'No books waiting',
			description: 'Books you want to read will appear here.',
			cta: { label: 'Discover books', href: '/discover' }
		},
		READING: {
			title: 'Not reading anything right now',
			description: 'Books you are currently reading will appear here.'
		},
		READ: {
			title: 'No finished books yet',
			description: 'Books you have finished will appear here.'
		}
	};

	const filtered = $derived(entries.filter((e) => e.status === activeTab));
	const tabCounts = $derived({
		WANT_TO_READ: entries.filter((e) => e.status === 'WANT_TO_READ').length,
		READING: entries.filter((e) => e.status === 'READING').length,
		READ: entries.filter((e) => e.status === 'READ').length
	});

	$effect(() => {
		const p = page.url.searchParams.get('tab');
		if (p === 'reading') activeTab = 'READING';
		else if (p === 'read') activeTab = 'READ';
		else if (p === 'want-to-read') activeTab = 'WANT_TO_READ';
	});

	function setTab(id: ShelfStatus) {
		activeTab = id;
		const url = new URL(page.url);
		url.searchParams.set(
			'tab',
			{ WANT_TO_READ: 'want-to-read', READING: 'reading', READ: 'read' }[id]
		);
		goto(url, { replaceState: true, noScroll: true, keepFocus: true });
	}

	async function handleStatusChange(entryId: number, newStatus: ShelfStatus) {
		const i = entries.findIndex((e) => e.id === entryId);
		if (i === -1) return;
		const prev = entries[i].status;
		entries[i] = { ...entries[i], status: newStatus };
		const { error } = await updateShelfEntry(fetch, entryId, { status: newStatus });
		if (error) {
			entries[i] = { ...entries[i], status: prev };
			toast.error('Failed to update status');
		}
	}

	async function handleRate(bookSlug: string, rating: number, entryId: number) {
		const i = entries.findIndex((e) => e.id === entryId);
		if (i === -1) return;
		const entry = entries[i];

		// Same star → un-rate
		if (rating === entry.user_rating && entry.rating_id != null) {
			entries[i] = { ...entry, user_rating: null, rating_id: null };
			const { error } = await deleteRatingById(fetch, entry.rating_id);
			if (error) {
				entries[i] = entry;
				toast.error('Failed to remove rating');
			}
			return;
		}
		entries[i] = { ...entry, user_rating: rating };
		const { data: result, error } = await upsertRating(fetch, bookSlug, rating);
		if (error || !result) {
			entries[i] = entry;
			toast.error('Failed to save rating');
		} else {
			entries[i] = { ...entries[i], user_rating: result.rating, rating_id: result.id };
		}
	}

	async function handleProgressChange(entryId: number, currentPage: number) {
		const i = entries.findIndex((e) => e.id === entryId);
		if (i === -1) return;
		const prev = entries[i].current_page;
		entries[i] = { ...entries[i], current_page: currentPage };
		const { error } = await updateShelfEntry(fetch, entryId, { current_page: currentPage });
		if (error) {
			entries[i] = { ...entries[i], current_page: prev };
			toast.error('Failed to update progress');
		}
	}

	async function handleDelete(entryId: number) {
		const i = entries.findIndex((e) => e.id === entryId);
		if (i === -1) return;
		const removed = entries[i];
		entries = entries.filter((e) => e.id !== entryId);
		const { error } = await deleteShelfEntry(fetch, entryId);
		if (error) {
			entries = [...entries.slice(0, i), removed, ...entries.slice(i)];
			toast.error('Failed to remove book');
		}
	}
</script>

<svelte:head><title>My Shelf — Storyshelf</title></svelte:head>

<main class="max-w-[1240px] mx-auto px-6 md:px-10 py-10 space-y-6">
	<div>
		<h1 class="font-display text-3xl md:text-4xl tracking-tight font-medium text-ink">My Shelf</h1>
		<p class="text-sm text-muted mt-1">Track what you read and want to read.</p>
	</div>

	<div class="flex border-b border-rule" role="tablist">
		<button
			type="button"
			role="tab"
			data-testid="shelf-view-tab"
			data-view="status"
			aria-selected={viewTab === 'status'}
			aria-controls="panel-status"
			class="flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors {viewTab ===
			'status'
				? 'border-accent text-accent'
				: 'border-transparent text-muted hover:text-ink hover:border-rule'}"
			onclick={() => (viewTab = 'status')}
		>
			<span>Reading status</span>
		</button>
		<button
			type="button"
			role="tab"
			data-testid="shelf-view-tab"
			data-view="shelves"
			aria-selected={viewTab === 'shelves'}
			aria-controls="panel-shelves"
			class="flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors {viewTab ===
			'shelves'
				? 'border-accent text-accent'
				: 'border-transparent text-muted hover:text-ink hover:border-rule'}"
			onclick={() => (viewTab = 'shelves')}
		>
			<span>My shelves</span>
		</button>
	</div>

	{#if viewTab === 'status'}
		<div class="flex border-b border-rule" role="tablist">
			{#each tabs as tab (tab.id)}
				<button
					type="button"
					role="tab"
					data-testid="shelf-tab"
					data-tab={tab.id.toLowerCase()}
					aria-selected={activeTab === tab.id}
					aria-controls="panel-status"
					class="flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors {activeTab ===
					tab.id
						? 'border-accent text-accent'
						: 'border-transparent text-muted hover:text-ink hover:border-rule'}"
					onclick={() => setTab(tab.id)}
				>
					<tab.icon class="size-4" />
					<span>{tab.label}</span>
					<span
						class="ml-1 rounded-full bg-paper-2 px-1.5 py-0.5 text-[10px] font-medium text-muted leading-none"
						>{tabCounts[tab.id]}</span
					>
				</button>
			{/each}
		</div>

		<div id="panel-status" role="tabpanel">
			{#if filtered.length > 0}
				<div class="space-y-3">
					{#each filtered as entry (entry.id)}
						<ShelfBookCard
							{entry}
							onDelete={handleDelete}
							onRate={handleRate}
							onStatusChange={handleStatusChange}
							onProgressChange={handleProgressChange}
						/>
					{/each}
				</div>
			{:else}
				{@const msg = emptyMessages[activeTab]}
				<div data-testid="shelf-empty">
					<EmptyState
						icon={tabs.find((t) => t.id === activeTab)?.icon ?? BookOpen}
						title={msg.title}
						description={msg.description}
						cta={msg.cta}
					/>
				</div>
			{/if}
		</div>
	{:else}
		<div id="panel-shelves" role="tabpanel" class="space-y-6">
			<form
				class="flex flex-wrap items-end gap-3"
				onsubmit={(e) => {
					e.preventDefault();
					handleCreate();
				}}
			>
				<div class="flex-1 min-w-[200px] space-y-1.5">
					<Label for="shelf-name">Shelf name</Label>
					<Input id="shelf-name" name="name" bind:value={newName} data-testid="shelf-name-input" />
				</div>
				<label class="flex items-center gap-2 py-2.5 text-sm text-ink">
					<input type="checkbox" bind:checked={newPublic} data-testid="shelf-public-input" />
					<span>Public</span>
				</label>
				<Button type="submit" disabled={creating} data-testid="shelf-create-submit">Create</Button>
			</form>

			{#if createError}
				<p class="text-sm text-danger" data-testid="shelf-create-error">{createError}</p>
			{/if}

			{#if shelves.length > 0}
				<div class="space-y-3">
					{#each shelves as shelf (shelf.id)}
						<a
							href="/shelf/{shelf.slug}"
							data-testid="shelf-card"
							class="flex items-center justify-between rounded-lg border border-rule bg-paper px-4 py-3 transition-colors hover:border-accent"
						>
							<div>
								<span class="font-medium text-ink">{shelf.name}</span>
								<span class="ml-2 text-sm text-muted">{shelf.book_count} books</span>
							</div>
							{#if shelf.is_public}
								<span
									class="rounded-full bg-paper-2 px-2 py-0.5 text-[10px] font-medium text-muted leading-none"
									>Public</span
								>
							{/if}
						</a>
					{/each}
				</div>
			{:else}
				<div data-testid="shelves-empty">
					<EmptyState
						icon={Library}
						title="No shelves yet"
						description="Create your first shelf to organize books your way."
					/>
				</div>
			{/if}
		</div>
	{/if}
</main>
