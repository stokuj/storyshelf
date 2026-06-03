<script lang="ts">
	import Avatar from '$lib/components/Avatar.svelte';
	import type { FollowUser } from '$lib/types/follow';

	let { user }: { user: FollowUser } = $props();
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
</a>
