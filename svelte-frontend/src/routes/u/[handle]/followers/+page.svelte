<script lang="ts">
	import type { PageProps } from './$types';
	import FollowList from '$lib/components/FollowList.svelte';

	let { data }: PageProps = $props();
</script>

<svelte:head>
	<title>Followers of @{data.handle} — Storyshelf</title>
</svelte:head>

<div class="max-w-[680px] mx-auto px-6 md:px-10 py-8">
	<a href="/u/{data.handle}" class="text-sm text-muted hover:text-ink transition-colors"
		>← @{data.handle}</a
	>
	<h1 class="font-display text-2xl font-medium text-ink mt-2 mb-5">Followers</h1>
	<FollowList users={data.users} emptyText="No followers yet." />
</div>
