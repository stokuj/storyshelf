<script lang="ts">
	import type { PageProps } from './$types';
	import Avatar from '$lib/components/Avatar.svelte';
	import { Button } from '$lib/components/ui/button';
	import { Calendar } from 'lucide-svelte';
	import type { User } from '$lib/types';

	let { data }: PageProps = $props();
	let profile: User = $derived(data.profile!);
	let isOwner = $derived(data.isOwner);
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
			</div>
		</div>

		{#if isOwner}
			<Button variant="outline" size="sm" href="/settings">Edit profile</Button>
		{/if}
	</div>
</div>
