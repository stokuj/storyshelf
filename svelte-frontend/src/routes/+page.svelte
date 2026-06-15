<script lang="ts">
	import { page } from '$app/state';
	import { Button } from '$lib/components/ui/button';
	import BookCover from '$lib/components/book/BookCover.svelte';
	import ProgressBar from '$lib/components/shelf/ProgressBar.svelte';
	import FeedItem from '$lib/components/feed/FeedItem.svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import { BookOpen } from 'lucide-svelte';
	import type { UserMe } from '$lib/api/user';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	let user = $derived(page.data.user as UserMe | null | undefined);
</script>

<svelte:head>
	<title>Home — Storyshelf</title>
</svelte:head>

<main class="max-w-[1240px] mx-auto px-6 md:px-10 py-10 space-y-12">
	<header>
		<h1 class="font-display text-4xl md:text-5xl tracking-tight font-medium text-ink mb-2">
			Welcome back{user?.display_name ? `, ${user.display_name}` : ''}
		</h1>
		<p class="text-ink-2 text-[15px] leading-relaxed">Pick up where you left off.</p>
	</header>

	<!-- Continue reading -->
	<section>
		<div class="flex items-center justify-between mb-4">
			<h2 class="font-display text-2xl font-medium text-ink">Continue reading</h2>
			<Button variant="ghost" size="sm" href="/shelf">View shelf</Button>
		</div>

		{#if data.reading.length > 0}
			<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
				{#each data.reading as entry (entry.id)}
					<a
						href="/books/{entry.book.slug}"
						class="block rounded-lg border border-rule bg-surface p-3 shadow-sm hover:shadow-md transition-shadow"
					>
						<div class="flex gap-3">
							<BookCover coverUrl={entry.book.cover_url} title={entry.book.title} size="sm" />
							<div class="min-w-0 flex-1">
								<h3 class="font-sans text-sm font-semibold text-ink line-clamp-2">
									{entry.book.title}
								</h3>
								<p class="text-xs text-muted line-clamp-1">{entry.book.authors.join(', ')}</p>
							</div>
						</div>
						<div class="mt-3">
							<ProgressBar current={entry.current_page} total={entry.book.page_count} />
						</div>
					</a>
				{/each}
			</div>
		{:else}
			<EmptyState
				icon={BookOpen}
				title="Nothing in progress"
				description="Mark a book as “Reading” to see it here."
				cta={{ label: 'Discover books', href: '/discover' }}
			/>
		{/if}
	</section>

	<!-- Recent activity -->
	{#if data.feedItems.length > 0}
		<section>
			<div class="flex items-center justify-between mb-4">
				<h2 class="font-display text-2xl font-medium text-ink">Recent activity</h2>
				<Button variant="ghost" size="sm" href="/feed">View feed</Button>
			</div>
			<div class="max-w-[700px]">
				{#each data.feedItems as item (item.type + item.actor.handle + item.book.slug + item.timestamp)}
					<FeedItem {item} />
				{/each}
			</div>
		</section>
	{/if}
</main>
