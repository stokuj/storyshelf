<script lang="ts">
	import type { PageProps } from './$types';
	import Avatar from '$lib/components/Avatar.svelte';
	import { Button } from '$lib/components/ui/button';
	import FollowButton from '$lib/components/FollowButton.svelte';
	import ReviewCard from '$lib/components/review/ReviewCard.svelte';
	import { Calendar } from 'lucide-svelte';
	import type { User } from '$lib/types';
	import type { PublicShelf, ShelfEntry } from '$lib/types/shelf';
	import type { Review } from '$lib/types/review';

	let { data }: PageProps = $props();
	let profile: User = $derived(data.profile!);
	let isOwner = $derived(data.isOwner);
	let isLoggedIn = $derived(data.isLoggedIn);
	let shelves: PublicShelf[] = $derived(data.shelves);
	let reading: ShelfEntry[] = $derived(data.reading);
	let reviews: Review[] = $derived(data.reviews);

	const STATUS_LABEL: Record<string, string> = {
		WANT_TO_READ: 'Want to read',
		READING: 'Reading',
		READ: 'Read'
	};
	// Writable $derived: optimistic count updates from FollowButton override locally,
	// and it auto-resyncs when navigating to another profile.
	let followersCount = $derived(profile.followers_count);
</script>

<svelte:head>
	<title>{profile.display_name ?? profile.handle} — Storyshelf</title>
</svelte:head>

<div class="max-w-[1240px] mx-auto px-6 md:px-10 py-8">
	<div class="flex items-start gap-5">
		<Avatar
			name={profile.display_name ?? profile.handle}
			avatarUrl={profile.avatar_url}
			size="xl"
		/>
		<div class="flex-1">
			<h1 class="font-display text-3xl font-medium text-ink">
				{profile.display_name ?? profile.handle}
			</h1>
			<p class="text-muted">@{profile.handle}</p>
			{#if profile.bio}
				<p class="text-sm text-ink-2 mt-2 max-w-lg">{profile.bio}</p>
			{/if}
			<div class="flex items-center gap-4 mt-3 text-sm text-muted">
				<span class="inline-flex items-center gap-1">
					<Calendar class="size-3.5" />
					Joined {new Date(profile.member_since).getFullYear()}
				</span>
				<a href="/u/{profile.handle}/followers" class="hover:text-ink transition-colors">
					<span class="font-medium text-ink">{followersCount}</span> Followers
				</a>
				<a href="/u/{profile.handle}/following" class="hover:text-ink transition-colors">
					<span class="font-medium text-ink">{profile.following_count}</span> Following
				</a>
			</div>
		</div>

		{#if isOwner}
			<Button variant="outline" size="sm" href="/settings">Edit profile</Button>
		{:else if isLoggedIn}
			<FollowButton
				handle={profile.handle}
				isFollowing={profile.is_following}
				onFollowChange={(f) => (followersCount += f ? 1 : -1)}
			/>
		{/if}
	</div>

	{#if shelves.length > 0}
		<section class="mt-10">
			<h2 class="font-display text-xl font-medium text-ink mb-4">Shelves</h2>
			<ul class="flex flex-col gap-2">
				{#each shelves as shelf (shelf.slug)}
					<li>
						<a
							href="/u/{profile.handle}/shelves/{shelf.slug}"
							class="flex items-center justify-between rounded-lg border border-rule bg-surface px-4 py-3 hover:bg-paper-2 transition-colors"
						>
							<span class="text-ink font-medium">{shelf.name}</span>
							<span class="text-sm text-muted">{shelf.book_count} books</span>
						</a>
					</li>
				{/each}
			</ul>
		</section>
	{/if}

	{#if reading.length > 0}
		<section class="mt-10">
			<h2 class="font-display text-xl font-medium text-ink mb-4">Reading</h2>
			<ul class="flex flex-col gap-2">
				{#each reading as entry (entry.book.slug)}
					<li>
						<a
							href="/books/{entry.book.slug}"
							class="flex items-center gap-3 rounded-lg border border-rule bg-surface px-4 py-3 hover:bg-paper-2 transition-colors"
						>
							{#if entry.book.cover_url}
								<img
									src={entry.book.cover_url}
									alt=""
									class="h-12 w-8 shrink-0 rounded object-cover"
								/>
							{/if}
							<div class="min-w-0 flex-1">
								<p class="text-ink font-medium truncate">{entry.book.title}</p>
								<p class="text-sm text-muted truncate">{entry.book.authors.join(', ')}</p>
							</div>
							{#if entry.user_rating}
								<span class="shrink-0 text-sm text-muted">★ {entry.user_rating}</span>
							{/if}
							<span class="shrink-0 rounded-full border border-rule px-2 py-0.5 text-xs text-muted">
								{STATUS_LABEL[entry.status]}
							</span>
						</a>
					</li>
				{/each}
			</ul>
		</section>
	{/if}

	{#if reviews.length > 0}
		<section class="mt-10">
			<h2 class="font-display text-xl font-medium text-ink mb-4">Reviews</h2>
			{#each reviews as review (review.id)}
				<ReviewCard {review} canLike={isLoggedIn} />
			{/each}
		</section>
	{/if}
</div>
