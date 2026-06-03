<script lang="ts">
	import UserRow from '$lib/components/UserRow.svelte';
	import type { FollowUser } from '$lib/types/follow';

	let { users, emptyText }: { users: FollowUser[]; emptyText: string } = $props();
</script>

{#if users.length === 0}
	<p class="text-muted text-sm">{emptyText}</p>
{:else}
	<ul class="flex flex-col gap-2">
		{#each users as user (user.handle)}
			<li><UserRow {user} /></li>
		{/each}
	</ul>
{/if}
