<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import { goto } from '$app/navigation';
	import { Search } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import UserMenu from './UserMenu.svelte';
	import type { UserMe } from '$lib/api/user';

	interface Props {
		children: import('svelte').Snippet;
	}

	let { children }: Props = $props();

	let user: UserMe | null | undefined = $derived(page.data.user as UserMe | null | undefined);

	let searchQuery = $state('');

	function submitSearch(e: SubmitEvent) {
		e.preventDefault();
		const q = searchQuery.trim();
		goto(`/discover${q ? `?q=${encodeURIComponent(q)}` : ''}`);
	}
</script>

<a
	href="#main-content"
	class="sr-only focus:not-sr-only focus:absolute focus:z-[60] focus:top-3 focus:left-3 focus:bg-ink focus:text-paper focus:px-4 focus:py-2 focus:rounded-md"
>
	Skip to content
</a>

<header class="sticky top-0 z-50 bg-paper/80 backdrop-blur border-b border-rule">
	<div class="max-w-[1240px] mx-auto px-6 md:px-10 flex items-center justify-between h-14">
		<!-- Left: brand + nav -->
		<div class="flex items-center gap-6">
			<a href={resolve('/')} class="font-display text-xl font-semibold text-ink tracking-tight">
				Storyshelf
			</a>
			<nav class="hidden md:flex items-center gap-1">
				<Button variant="ghost" size="sm" href={resolve('/discover')}>Discover</Button>
				<Button variant="ghost" size="sm" href={resolve('/users')}>People</Button>
				{#if user}
					<Button variant="ghost" size="sm" href={resolve('/feed')}>Feed</Button>
					<Button variant="ghost" size="sm" href={resolve('/shelf')}>Shelf</Button>
					<Button variant="ghost" size="sm" href={resolve('/stats')}>Stats</Button>
				{/if}
			</nav>
		</div>

		<!-- Right: search + user -->
		<div class="flex items-center gap-2">
			<form onsubmit={submitSearch} class="hidden sm:block relative">
				<Search
					class="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted pointer-events-none"
				/>
				<Input
					class="pl-8 h-9 w-40 lg:w-56"
					type="search"
					placeholder="Search…"
					aria-label="Search books"
					bind:value={searchQuery}
				/>
			</form>
			<UserMenu {user} />
		</div>
	</div>
</header>

<main id="main-content" class="min-h-screen">
	{@render children()}
</main>
