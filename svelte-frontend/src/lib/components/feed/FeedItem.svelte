<script lang="ts">
	import type { FeedItem } from '$lib/types/feed';
	import Avatar from '$lib/components/Avatar.svelte';

	interface Props {
		item: FeedItem;
	}
	let { item }: Props = $props();

	const date = $derived(new Date(item.timestamp).toLocaleDateString());

	const actionLabel = $derived(
		item.type === 'rating'
			? `rated ${item.rating}/5`
			: item.type === 'review'
				? 'reviewed'
				: 'finished'
	);
</script>

<article data-testid="feed-item" class="border-b border-rule py-4 flex gap-3">
	<a href="/u/{item.actor.handle}" class="shrink-0">
		<Avatar
			name={item.actor.display_name || item.actor.handle}
			avatarUrl={item.actor.avatar_url}
			size="sm"
		/>
	</a>
	<div class="min-w-0 flex-1">
		<p class="text-sm">
			<a href="/u/{item.actor.handle}" class="font-medium hover:text-accent transition-colors"
				>{item.actor.display_name || `@${item.actor.handle}`}</a
			>
			{actionLabel}
			<a href="/books/{item.book.slug}" class="font-medium hover:text-accent transition-colors"
				>{item.book.title}</a
			>
		</p>
		{#if item.type === 'review' && item.body}
			<p class="mt-1 text-sm text-ink-2 line-clamp-3 whitespace-pre-wrap">{item.body}</p>
		{/if}
		<time class="mt-1 block text-xs text-muted">{date}</time>
	</div>
	{#if item.book.cover_url}
		<a href="/books/{item.book.slug}" class="shrink-0">
			<img src={item.book.cover_url} alt="" class="h-14 w-10 rounded object-cover" />
		</a>
	{/if}
</article>
