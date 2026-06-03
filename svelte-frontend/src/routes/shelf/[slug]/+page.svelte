<script lang="ts">
	import { goto, invalidateAll } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { Library } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import { updateShelf, deleteShelf, removeBookFromShelf } from '$lib/api/shelves';
	import type { ShelfDetail } from '$lib/types/shelf';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	// Mirrors loader data (re-fetched via invalidateAll() after mutations). Never mutated
	// in place — only reassigned — so a writable $derived is safe (no in-place gotcha).
	let shelf = $derived<ShelfDetail>(data.shelf);

	// Form fields seeded once from loader data; user edits are kept after invalidateAll().
	// svelte-ignore state_referenced_locally
	let name = $state(data.shelf.name);
	// svelte-ignore state_referenced_locally
	let description = $state(data.shelf.description);
	// svelte-ignore state_referenced_locally
	let isPublic = $state(data.shelf.is_public);
	let saving = $state(false);
	let saveError = $state('');

	async function save() {
		if (!name.trim()) return;
		saving = true;
		saveError = '';
		const { error } = await updateShelf(fetch, shelf.slug, {
			name: name.trim(),
			description,
			is_public: isPublic
		});
		saving = false;
		if (error) {
			saveError = error.detail;
			return;
		}
		toast.success('Shelf saved');
		await invalidateAll();
	}

	async function remove(bookSlug: string) {
		const { error } = await removeBookFromShelf(fetch, shelf.slug, bookSlug);
		if (error) {
			toast.error('Failed to remove book');
			return;
		}
		await invalidateAll();
	}

	async function destroy() {
		if (!confirm(`Delete shelf "${shelf.name}"?`)) return;
		const { error } = await deleteShelf(fetch, shelf.slug);
		if (error) {
			toast.error('Failed to delete shelf');
			return;
		}
		await goto('/shelf');
	}
</script>

<svelte:head><title>{shelf.name} — Storyshelf</title></svelte:head>

<main class="max-w-[1240px] mx-auto px-6 md:px-10 py-10 space-y-8">
	<div class="flex items-start justify-between gap-4">
		<div>
			<h1 class="font-display text-3xl md:text-4xl tracking-tight font-medium text-ink">
				{shelf.name}
			</h1>
			<p class="text-sm text-muted mt-1">{shelf.book_count} books</p>
		</div>
		<Button variant="outline" onclick={destroy} data-testid="shelf-delete">Delete shelf</Button>
	</div>

	<form
		class="space-y-4 rounded-lg border border-rule bg-paper p-5"
		onsubmit={(e) => {
			e.preventDefault();
			save();
		}}
	>
		<div class="space-y-1.5">
			<Label for="shelf-name">Shelf name</Label>
			<Input id="shelf-name" name="name" bind:value={name} data-testid="shelf-name-input" />
		</div>
		<div class="space-y-1.5">
			<Label for="shelf-description">Description</Label>
			<textarea
				id="shelf-description"
				bind:value={description}
				data-testid="shelf-description-input"
				rows="3"
				class="w-full rounded border border-rule bg-transparent p-2 text-sm"
			></textarea>
		</div>
		<label class="flex items-center gap-2 text-sm text-ink">
			<input type="checkbox" bind:checked={isPublic} data-testid="shelf-public-input" />
			<span>Public</span>
		</label>
		<div class="flex items-center gap-3">
			<Button type="submit" disabled={saving} data-testid="shelf-save-submit">Save</Button>
			{#if saveError}
				<p class="text-sm text-danger" data-testid="shelf-save-error">{saveError}</p>
			{/if}
		</div>
	</form>

	<section class="space-y-3">
		<h2 class="font-display text-xl tracking-tight font-medium text-ink">Books</h2>
		{#if shelf.books.length > 0}
			<div class="space-y-3" data-testid="shelf-books">
				{#each shelf.books as book (book.slug)}
					<div
						class="flex items-center justify-between rounded-lg border border-rule bg-paper px-4 py-3"
						data-testid="shelf-book"
					>
						<a
							href="/books/{book.slug}"
							class="font-medium text-ink transition-colors hover:text-accent"
						>
							{book.title}
						</a>
						<Button
							variant="outline"
							size="sm"
							onclick={() => remove(book.slug)}
							data-testid="shelf-book-remove">Remove from shelf</Button
						>
					</div>
				{/each}
			</div>
		{:else}
			<div data-testid="shelf-books-empty">
				<EmptyState
					icon={Library}
					title="Empty shelf"
					description="Add books to this shelf from a book's page."
				/>
			</div>
		{/if}
	</section>
</main>
