<script lang="ts">
	import { Input } from '$lib/components/ui/input';
	import { Search, ChevronDown } from 'lucide-svelte';
	import type { Genre } from '$lib/api/books';

	interface Props {
		query: string;
		genre: string;
		sort: string;
		genres: Genre[];
		onsearch: (q: string) => void;
		ongenrechange: (genre: string) => void;
		onsortchange: (sort: string) => void;
	}

	let { query, genre, sort, genres, onsearch, ongenrechange, onsortchange }: Props = $props();

	const SORT_OPTIONS = [
		{ value: '', label: 'Sort' },
		{ value: 'title', label: 'Title' },
		{ value: 'rating', label: 'Rating' },
		{ value: 'recent', label: 'Recent' }
	];

	let genreOpen = $state(false);
	let sortOpen = $state(false);

	let genreEl: HTMLElement | undefined = $state();
	let sortEl: HTMLElement | undefined = $state();

	let debounceTimer: ReturnType<typeof setTimeout>;

	function handleSearchInput(e: Event) {
		clearTimeout(debounceTimer);
		const value = (e.target as HTMLInputElement).value;
		debounceTimer = setTimeout(() => {
			onsearch(value);
		}, 300);
	}

	function selectGenre(value: string) {
		genreOpen = false;
		ongenrechange(value);
	}

	function selectSort(value: string) {
		sortOpen = false;
		onsortchange(value);
	}

	let genreLabel = $derived(
		genres.find((g) => g.name === genre)?.name ?? (genre ? genre : 'Genre')
	);

	let sortLabel = $derived(SORT_OPTIONS.find((o) => o.value === sort)?.label ?? 'Sort');
</script>

<div class="flex flex-wrap items-center gap-3 mb-8">
	<!-- Search -->
	<div class="relative flex-1 min-w-[200px] max-w-sm">
		<Search
			class="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted pointer-events-none"
		/>
		<Input class="pl-8" placeholder="Search books…" value={query} oninput={handleSearchInput} />
	</div>

	<!-- Genre dropdown -->
	<div class="relative" bind:this={genreEl}>
		<button
			class="flex h-9 w-[140px] items-center justify-between rounded-md border border-rule bg-surface px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
			class:text-ink={genre !== ''}
			class:text-muted={genre === ''}
			type="button"
			onclick={() => {
				genreOpen = !genreOpen;
				sortOpen = false;
			}}
		>
			<span class="truncate">{genreLabel}</span>
			<ChevronDown class="size-4 ml-1 shrink-0 text-muted" />
		</button>
		{#if genreOpen}
			<div
				class="absolute left-0 top-full z-50 mt-1 min-w-[8rem] w-[160px] overflow-hidden rounded-md border border-rule bg-surface p-1 shadow-md"
				role="listbox"
			>
				<button
					class="relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm text-ink outline-none hover:bg-paper-2"
					type="button"
					onclick={() => selectGenre('')}
				>
					All genres
				</button>
				{#each genres as g (g.id)}
					<button
						class="relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm text-ink outline-none hover:bg-paper-2"
						type="button"
						onclick={() => selectGenre(g.name)}
					>
						{g.name}
					</button>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Sort dropdown -->
	<div class="relative" bind:this={sortEl}>
		<button
			class="flex h-9 w-[130px] items-center justify-between rounded-md border border-rule bg-surface px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
			class:text-ink={sort !== ''}
			class:text-muted={sort === ''}
			type="button"
			onclick={() => {
				sortOpen = !sortOpen;
				genreOpen = false;
			}}
		>
			<span class="truncate">{sortLabel}</span>
			<ChevronDown class="size-4 ml-1 shrink-0 text-muted" />
		</button>
		{#if sortOpen}
			<div
				class="absolute left-0 top-full z-50 mt-1 min-w-[8rem] w-[140px] overflow-hidden rounded-md border border-rule bg-surface p-1 shadow-md"
				role="listbox"
			>
				{#each SORT_OPTIONS.slice(1) as option (option.value)}
					<button
						class="relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm text-ink outline-none hover:bg-paper-2"
						type="button"
						onclick={() => selectSort(option.value)}
					>
						{option.label}
					</button>
				{/each}
			</div>
		{/if}
	</div>
</div>

<svelte:window
	onclick={(e: MouseEvent) => {
		const target = e.target as Node;
		if (genreEl && !genreEl.contains(target) && sortEl && !sortEl.contains(target)) {
			genreOpen = false;
			sortOpen = false;
		}
	}}
/>
