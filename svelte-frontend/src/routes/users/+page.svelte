<script lang="ts">
	import UserRow from '$lib/components/UserRow.svelte';
	import { Button } from '$lib/components/ui/button';
	import { toast } from 'svelte-sonner';
	import { listUsers, type UserListItem } from '$lib/api/user';

	let { data } = $props();

	// Intentional one-time snapshot: this page self-manages search/ordering state
	// and refetches client-side, so it does not react to later `data`.
	// svelte-ignore state_referenced_locally
	const { initialUsers, initialTotal, initialSearch, initialOrdering, loadError } = data;

	if (loadError) {
		toast.error('Failed to load people', { description: loadError.detail });
	}

	let users = $state<UserListItem[]>(initialUsers);
	let total = $state<number>(initialTotal);
	let search = $state<string>(initialSearch);
	let ordering = $state<string>(initialOrdering);
	let currentPage = $state(1);
	let loading = $state(false);

	const hasMore = $derived(users.length < total);
	const PER_PAGE = 20;

	let debounce: ReturnType<typeof setTimeout> | undefined;

	async function reload() {
		loading = true;
		const { data: page } = await listUsers(fetch, {
			search: search || undefined,
			ordering,
			page: 1,
			perPage: PER_PAGE
		});
		users = page?.data ?? [];
		total = page?.total ?? 0;
		currentPage = 1;
		loading = false;
	}

	function onSearchInput() {
		clearTimeout(debounce);
		debounce = setTimeout(reload, 250);
	}

	function setOrdering(value: string) {
		if (ordering === value) return;
		ordering = value;
		reload();
	}

	async function loadMore() {
		loading = true;
		const next = currentPage + 1;
		const { data: page } = await listUsers(fetch, {
			search: search || undefined,
			ordering,
			page: next,
			perPage: PER_PAGE
		});
		users = [...users, ...(page?.data ?? [])];
		total = page?.total ?? total;
		currentPage = next;
		loading = false;
	}
</script>

<svelte:head>
	<title>People — Storyshelf</title>
</svelte:head>

<div class="max-w-[1240px] mx-auto px-6 md:px-10 py-8 space-y-6">
	<h1 class="font-display text-2xl font-semibold text-ink">People</h1>

	<div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
		<input
			type="search"
			placeholder="Search people"
			bind:value={search}
			oninput={onSearchInput}
			class="w-full sm:max-w-xs rounded-lg border border-rule bg-surface px-3 py-2 text-ink"
		/>
		<div class="flex gap-1">
			<Button
				variant={ordering === '-followers_count' ? 'default' : 'ghost'}
				size="sm"
				onclick={() => setOrdering('-followers_count')}
			>
				Most followed
			</Button>
			<Button
				variant={ordering === '-created_at' ? 'default' : 'ghost'}
				size="sm"
				onclick={() => setOrdering('-created_at')}
			>
				Newest
			</Button>
		</div>
	</div>

	{#if users.length === 0}
		<p class="text-muted text-sm">No people found.</p>
	{:else}
		<ul class="flex flex-col gap-2">
			{#each users as u (u.handle)}
				<li><UserRow user={u} followersCount={u.followers_count} /></li>
			{/each}
		</ul>
	{/if}

	{#if hasMore}
		<div class="flex justify-center">
			<Button variant="outline" size="sm" disabled={loading} onclick={loadMore}>
				{loading ? 'Loading…' : 'Load more'}
			</Button>
		</div>
	{/if}
</div>
