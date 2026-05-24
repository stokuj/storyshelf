<script lang="ts">
	import type { PageProps } from './$types';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import CharacterAvatar from '$lib/components/character/CharacterAvatar.svelte';
	import AIBadge from '$lib/components/ai/AIBadge.svelte';
	import { Input } from '$lib/components/ui/input';
	import { Search, Users } from 'lucide-svelte';
	import type { Character } from '$lib/types';

	let { data }: PageProps = $props();
	let book = $derived(data.book!);
	let allCharacters: Character[] = $derived(data.characters ?? []);

	let search = $state('');
	let roleFilter = $state('');

	let filteredCharacters = $derived(
		allCharacters.filter((c) => {
			if (search && !c.name.toLowerCase().includes(search.toLowerCase())) return false;
			if (roleFilter && c.role !== roleFilter) return false;
			return true;
		})
	);

	let focusCharId = $derived($page.url.searchParams.get('focus'));

	function selectCharacter(charId: number) {
		const url = new URL($page.url);
		url.searchParams.set('focus', String(charId));
		goto(url, { keepFocus: true });
	}

	const roles: string[] = ['protagonist', 'antagonist', 'supporting', 'minor'];
</script>

<svelte:head>
	<title>Characters in {book.title} — Storyshelf</title>
</svelte:head>

<div class="max-w-[1240px] mx-auto px-6 md:px-10 py-8">
	<div class="mb-6">
		<a href="/books/{book.slug}" class="text-sm text-muted hover:text-accent">
			← Back to {book.title}
		</a>
		<h1 class="font-display text-3xl font-medium text-ink mt-1">
			Characters in {book.title}
		</h1>
	</div>

	<!-- Mobile: stacked -->
	<div class="lg:hidden space-y-6">
		<div class="flex gap-2">
			<div class="relative flex-1">
				<Search class="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted" />
				<Input class="pl-8" placeholder="Search characters…" bind:value={search} />
			</div>
		</div>

		<!-- Role filter pills -->
		<div class="flex flex-wrap gap-1.5">
			<button
				class="px-2.5 py-0.5 rounded-full text-xs font-medium transition-colors"
				class:bg-ink={roleFilter === ''}
				class:text-paper={roleFilter === ''}
				class:bg-rule={roleFilter !== ''}
				class:text-ink={roleFilter !== ''}
				onclick={() => (roleFilter = '')}
			>
				All
			</button>
			{#each roles as role}
				<button
					class="px-2.5 py-0.5 rounded-full text-xs font-medium capitalize transition-colors"
					class:bg-ink={roleFilter === role}
					class:text-paper={roleFilter === role}
					class:bg-rule={roleFilter !== role}
					class:text-ink={roleFilter !== role}
					onclick={() => (roleFilter = role)}
				>
					{role}
				</button>
			{/each}
		</div>

		<div class="space-y-2">
			{#each filteredCharacters as char (char.id)}
				<button
					class="w-full text-left flex items-center gap-3 p-3 rounded-md border border-rule hover:border-rule-strong transition-colors"
					class:bg-accent-soft={String(char.id) === focusCharId}
					onclick={() => selectCharacter(char.id)}
				>
					<CharacterAvatar name={char.name} size="sm" />
					<div class="flex-1 min-w-0">
						<div class="flex items-center gap-1.5">
							<span class="text-sm font-medium text-ink">{char.name}</span>
							{#if char.source !== 'ai-verified' && char.source !== 'human'}
								<AIBadge />
							{/if}
						</div>
						<span class="text-xs text-muted capitalize">{char.role}</span>
					</div>
				</button>
			{/each}
			{#if filteredCharacters.length === 0}
				<div class="text-center py-12 text-sm text-muted">
					<Users class="size-8 mx-auto mb-2" />
					<p>No characters found matching your filters.</p>
				</div>
			{/if}
		</div>
	</div>

	<!-- Desktop: 2-column -->
	<div class="hidden lg:grid lg:grid-cols-[320px_1fr] gap-8">
		<!-- Left: character list -->
		<div class="space-y-4">
			<div class="flex gap-2">
				<div class="relative flex-1">
					<Search class="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted" />
					<Input class="pl-8" placeholder="Search characters…" bind:value={search} />
				</div>
			</div>

			<!-- Role filter pills -->
			<div class="flex flex-wrap gap-1.5">
				<button
					class="px-2.5 py-0.5 rounded-full text-xs font-medium transition-colors"
					class:bg-ink={roleFilter === ''}
					class:text-paper={roleFilter === ''}
					class:bg-rule={roleFilter !== ''}
					class:text-ink={roleFilter !== ''}
					onclick={() => (roleFilter = '')}
				>
					All
				</button>
				{#each roles as role}
					<button
						class="px-2.5 py-0.5 rounded-full text-xs font-medium capitalize transition-colors"
						class:bg-ink={roleFilter === role}
						class:text-paper={roleFilter === role}
						class:bg-rule={roleFilter !== role}
						class:text-ink={roleFilter !== role}
						onclick={() => (roleFilter = role)}
					>
						{role}
					</button>
				{/each}
			</div>

			<div class="space-y-1">
				{#each filteredCharacters as char (char.id)}
					<button
						class="w-full text-left flex items-center gap-3 p-2.5 rounded-md transition-colors"
						class:bg-accent-soft={String(char.id) === focusCharId}
						class:hover:bg-paper-2={String(char.id) !== focusCharId}
						onclick={() => selectCharacter(char.id)}
					>
						<CharacterAvatar name={char.name} size="sm" />
						<div class="flex-1 min-w-0">
							<div class="flex items-center gap-1.5">
								<span class="text-sm font-medium text-ink">{char.name}</span>
								{#if char.source !== 'ai-verified' && char.source !== 'human'}
									<AIBadge />
								{/if}
							</div>
							<span class="text-xs text-muted capitalize">{char.role}</span>
						</div>
					</button>
				{/each}
			</div>
		</div>

		<!-- Right: character detail -->
		<div class="border border-rule rounded-lg p-6 min-h-[300px]">
			{#if focusCharId}
				{@const char = allCharacters.find((c) => String(c.id) === focusCharId)}
				{#if char}
					<div class="space-y-4">
						<div class="flex items-center gap-4">
							<CharacterAvatar name={char.name} size="xl" />
							<div>
								<h2 class="font-display text-2xl font-medium text-ink">{char.name}</h2>
								{#if char.also_known_as?.length}
									<p class="text-sm text-muted">AKA: {char.also_known_as.join(', ')}</p>
								{/if}
								<div class="flex items-center gap-2 mt-1">
									<span
										class="inline-flex items-center rounded-full border border-rule px-2.5 py-0.5 text-xs font-semibold capitalize"
									>
										{char.role}
									</span>
									{#if char.source !== 'ai-verified' && char.source !== 'human'}
										<AIBadge />
									{/if}
								</div>
							</div>
						</div>
						<hr class="border-rule" />
						{#if char.short_bio}
							<div>
								<h3 class="font-sans text-sm font-semibold text-ink mb-1">About</h3>
								<p class="text-sm text-ink-2 leading-relaxed">{char.short_bio}</p>
							</div>
						{/if}
						{#if char.tags?.length}
							<div>
								<h3 class="font-sans text-sm font-semibold text-ink mb-1">Tags</h3>
								<div class="flex flex-wrap gap-1.5">
									{#each char.tags as tag}
										<span
											class="inline-flex items-center rounded-full border border-transparent bg-paper-2 px-2.5 py-0.5 text-xs font-semibold text-ink-2"
										>
											{tag}
										</span>
									{/each}
								</div>
							</div>
						{/if}
						{#if char.archetype}
							<div>
								<h3 class="font-sans text-sm font-semibold text-ink mb-1">Archetype</h3>
								<p class="text-sm text-muted capitalize">{char.archetype}</p>
							</div>
						{/if}
					</div>
				{:else}
					<p class="text-sm text-muted">Character not found.</p>
				{/if}
			{:else}
				<div class="flex items-center justify-center h-full">
					<div class="text-center text-muted">
						<Users class="size-10 mx-auto mb-2" />
						<p class="text-sm">Select a character from the list to see details.</p>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>
