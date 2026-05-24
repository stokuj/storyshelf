<script lang="ts">
	import type { PageProps } from './$types';
	import CharacterAvatar from '$lib/components/character/CharacterAvatar.svelte';
	import { Separator } from '$lib/components/ui/separator';
	import { Button } from '$lib/components/ui/button';
	import AIPanel from '$lib/components/ai/AIPanel.svelte';
	import { Calendar } from 'lucide-svelte';
	import type { User } from '$lib/types';

	let { data }: PageProps = $props();
	let profile: User = $derived(data.profile!);
	let shelves = $derived(data.shelves);
	let isOwner = $derived(data.isOwner);
</script>

<svelte:head>
	<title>{profile.display_name ?? profile.handle} — Storyshelf</title>
</svelte:head>

<div class="max-w-[1240px] mx-auto px-6 md:px-10 py-8">
	<div class="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-8">
		<!-- Main content -->
		<div class="space-y-8">
			<!-- Header -->
			<div class="flex items-start gap-5">
				<CharacterAvatar
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
							Joined {new Date(profile.joined_at).getFullYear()}
						</span>
						<span>{profile.followers_count} followers</span>
						<span>{profile.following_count} following</span>
					</div>
				</div>

				{#if isOwner}
					<Button variant="outline" size="sm" href="/settings">Edit profile</Button>
				{:else}
					<Button variant="outline" size="sm">Follow</Button>
				{/if}
			</div>

			<Separator />

			<!-- Reading challenge (placeholder) -->
			<div class="p-4 rounded-lg border border-rule bg-surface">
				<h2 class="font-display text-lg font-medium text-ink mb-2">Reading Challenge</h2>
				<div class="w-full bg-rule rounded-full h-2 mb-1">
					<div class="bg-accent rounded-full h-2" style="width: 60%"></div>
				</div>
				<p class="text-xs text-muted">12 / 20 books read this year</p>
			</div>

			<!-- Shelves -->
			{#if shelves.length > 0}
				<div>
					<h2 class="font-display text-xl font-medium text-ink mb-3">Shelves</h2>
					<div class="grid grid-cols-2 md:grid-cols-3 gap-3">
						{#each shelves as shelf (shelf.name)}
							<div class="p-3 rounded-md border border-rule bg-surface">
								<p class="text-sm font-medium text-ink">{shelf.name}</p>
								<p class="text-xs text-muted">{shelf.book_count} books</p>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>

		<!-- Right: AI sidecar -->
		<div class="space-y-4">
			<AIPanel title="AI Extractions">
				<p class="text-sm text-accent-ink/80">
					Recent AI extractions and character discoveries will appear here.
				</p>
				{#if isOwner}
					<Button variant="outline" size="sm" class="w-full mt-2" href="/settings/ai">
						AI preferences
					</Button>
				{/if}
			</AIPanel>
		</div>
	</div>
</div>
