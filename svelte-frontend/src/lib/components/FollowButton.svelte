<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { toast } from 'svelte-sonner';
	import { followUser, unfollowUser } from '$lib/api/follow';

	interface Props {
		handle: string;
		isFollowing: boolean;
		/**
		 * Reports the new follow state so the parent can adjust its follower count.
		 * Called optimistically on click; on a real failure it is called again with
		 * the reverted state. A parent that does `count += following ? 1 : -1` nets
		 * correctly across the optimistic+revert pair.
		 */
		onFollowChange?: (following: boolean) => void;
	}
	let { handle, isFollowing, onFollowChange }: Props = $props();

	// Writable $derived: assigning overrides locally (optimistic), and it
	// auto-resyncs to isFollowing when that prop changes (e.g. navigating to
	// another profile, where SvelteKit reuses this component).
	let following = $derived(isFollowing);
	let pending = $state(false);

	async function toggle() {
		if (pending) return;
		pending = true;
		const wasFollowing = following;
		following = !wasFollowing; // optimistic
		onFollowChange?.(following);

		const { error } = wasFollowing
			? await unfollowUser(fetch, handle)
			: await followUser(fetch, handle);

		// 409 (already following) / 404 (not following) == desired end state, keep optimistic.
		const realError = error && error.status !== 409 && error.status !== 404;
		if (realError) {
			following = wasFollowing;
			onFollowChange?.(following);
			toast.error('Something went wrong. Please try again.');
		}
		pending = false;
	}
</script>

<Button variant={following ? 'outline' : 'default'} size="sm" disabled={pending} onclick={toggle}>
	{following ? 'Unfollow' : 'Follow'}
</Button>
