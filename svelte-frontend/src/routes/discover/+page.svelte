<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import FilterBar from '$lib/components/discover/FilterBar.svelte';
	import BookGridDiscover from '$lib/components/discover/BookGridDiscover.svelte';
	import LoadMore from '$lib/components/discover/LoadMore.svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import { Button } from '$lib/components/ui/button';
	import { BookOpen, SearchX } from 'lucide-svelte';
	import { listBooks, fetchGenres } from '$lib/api/books';
	import type { Genre } from '$lib/api/books';
	import type { BookListItem } from '$lib/types/book';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	// Intentional one-time snapshot: this page self-manages pagination/filter
	// state and syncs the URL via goto(), so it does not react to later `data`.
	// svelte-ignore state_referenced_locally
	const {
		initialBooks,
		initialPage,
		initialPerPage,
		initialTotal,
		initialQ,
		initialGenre,
		initialSort,
		initialAuthor,
		loadError
	} = data;

	let books = $state<BookListItem[]>(initialBooks);
	let currentPage = $state(initialPage);
	let perPage = $state(initialPerPage);
	let total = $state(initialTotal);
	let loading = $state(false);
	let loadingMore = $state(false);
	let genres = $state<Genre[]>([]);

	let currentQ = $state(initialQ);
	let currentGenre = $state(initialGenre);
	let currentSort = $state(initialSort);
	// Set from the URL (e.g. author links on book pages); not edited in the UI,
	// but must persist across search/sort/load-more instead of being dropped.
	let currentAuthor = $state(initialAuthor);

	let hasFilters = $derived(
		currentQ !== '' || currentGenre !== '' || currentSort !== '' || currentAuthor !== ''
	);
	let hasMore = $derived(books.length < total);

	if (loadError) {
		toast.error('Failed to load books', {
			description: loadError.detail
		});
	}

	function buildUrl(): URL {
		const url = new URL(page.url);
		if (currentQ) url.searchParams.set('q', currentQ);
		else url.searchParams.delete('q');
		if (currentGenre) url.searchParams.set('genre', currentGenre);
		else url.searchParams.delete('genre');
		if (currentSort) url.searchParams.set('sort', currentSort);
		else url.searchParams.delete('sort');
		if (currentAuthor) url.searchParams.set('author', currentAuthor);
		else url.searchParams.delete('author');
		return url;
	}

	$effect(() => {
		if (genres.length === 0) {
			fetchGenres(fetch).then(({ data: result, error: apiErr }) => {
				if (result) genres = result.data;
				else if (apiErr) toast.error('Failed to load genres', { description: apiErr.detail });
			});
		}
	});

	async function loadBooks() {
		loading = true;
		const url = buildUrl();
		// Sync URL without adding history entry; noScroll + keepFocus prevent jarring jumps.
		goto(url, { replaceState: true, keepFocus: true, noScroll: true });

		const { data: result, error: apiErr } = await listBooks(fetch, {
			q: currentQ || undefined,
			genre: currentGenre || undefined,
			author: currentAuthor || undefined,
			sort: currentSort || undefined,
			page: 1,
			perPage
		});

		if (apiErr) {
			toast.error('Failed to load books', {
				description: apiErr.detail,
				action: { label: 'Retry', onClick: () => loadBooks() }
			});
		} else if (result) {
			books = result.data;
			currentPage = result.page;
			total = result.total;
		}
		loading = false;
	}

	async function loadMore() {
		loadingMore = true;
		const nextPage = currentPage + 1;

		const { data: result, error: apiErr } = await listBooks(fetch, {
			q: currentQ || undefined,
			genre: currentGenre || undefined,
			author: currentAuthor || undefined,
			sort: currentSort || undefined,
			page: nextPage,
			perPage
		});

		if (apiErr) {
			toast.error('Failed to load more', {
				description: apiErr.detail,
				action: { label: 'Retry', onClick: () => loadMore() }
			});
		} else if (result) {
			books = [...books, ...result.data];
			currentPage = result.page;
			total = result.total;
		}
		loadingMore = false;
	}

	function handleSearch(q: string) {
		currentQ = q;
		loadBooks();
	}

	function clearAuthor() {
		currentAuthor = '';
		loadBooks();
	}

	function handleGenreChange(genre: string) {
		currentGenre = genre;
		loadBooks();
	}

	function handleSortChange(sort: string) {
		currentSort = sort;
		loadBooks();
	}

	function clearFilters() {
		currentQ = '';
		currentGenre = '';
		currentSort = '';
		currentAuthor = '';
		loadBooks();
	}
</script>

<svelte:head>
	<title>Discover — Storyshelf</title>
	<meta name="description" content="Discover and track your favorite books on Storyshelf." />
</svelte:head>

<main class="max-w-[1240px] mx-auto px-6 md:px-10 py-10">
	<div class="mb-8">
		<h1 class="font-display text-4xl md:text-5xl tracking-tight font-medium text-ink mb-2">
			Discover
		</h1>
		<p class="text-ink-2 text-[15px] leading-relaxed">Browse books and find your next read.</p>
	</div>

	<FilterBar
		query={currentQ}
		genre={currentGenre}
		sort={currentSort}
		{genres}
		onsearch={handleSearch}
		ongenrechange={handleGenreChange}
		onsortchange={handleSortChange}
	/>

	{#if currentAuthor}
		<div class="mb-4 -mt-4">
			<span
				class="inline-flex items-center gap-1.5 rounded-full border border-rule bg-surface px-3 py-1 text-sm text-ink"
			>
				Author: {currentAuthor}
				<button
					type="button"
					aria-label="Clear author filter"
					class="text-muted hover:text-ink"
					onclick={clearAuthor}
				>
					×
				</button>
			</span>
		</div>
	{/if}

	{#if books.length > 0}
		<BookGridDiscover {books} loading={loading && books.length === 0} />
		<LoadMore loading={loadingMore} {hasMore} onloadmore={loadMore} />
	{:else if loading}
		<BookGridDiscover books={[]} loading />
	{:else if total === 0 && !hasFilters}
		<EmptyState
			icon={BookOpen}
			title="No books yet"
			description="The catalog is empty. Check back later for new additions."
		/>
	{:else}
		<EmptyState
			icon={SearchX}
			title="No books found"
			description="Try adjusting your search or filters."
			cta={{ label: 'Clear filters', href: '/discover' }}
		/>
		<div class="flex justify-center mt-2">
			<Button variant="ghost" size="sm" onclick={clearFilters}>Clear all filters</Button>
		</div>
	{/if}
</main>
