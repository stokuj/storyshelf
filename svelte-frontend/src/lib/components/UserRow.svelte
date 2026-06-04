<script lang="ts">
	import Avatar from '$lib/components/Avatar.svelte';

	// Structural type = common subset of FollowUser and UserListItem, so this row
	// is reusable by followers/following lists (no count) and /users (with count).
	let {
		user,
		followersCount
	}: {
		user: { handle: string; display_name: string; avatar_url: string | null };
		followersCount?: number;
	} = $props();
</script>

<a
	href="/u/{user.handle}"
	class="flex items-center gap-3 rounded-lg border border-rule bg-surface px-4 py-3 hover:bg-paper-2 transition-colors"
>
	<Avatar name={user.display_name || user.handle} avatarUrl={user.avatar_url} size="md" />
	<div class="min-w-0">
		<p class="text-ink font-medium truncate">{user.display_name || user.handle}</p>
		<p class="text-sm text-muted truncate">@{user.handle}</p>
	</div>
	{#if followersCount !== undefined}
		<span class="ml-auto shrink-0 text-sm text-muted">{followersCount} followers</span>
	{/if}
</a>
