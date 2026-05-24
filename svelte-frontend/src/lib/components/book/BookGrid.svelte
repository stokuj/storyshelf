<script lang="ts">
	import BookCard from './BookCard.svelte';

	interface BookCardData {
		id: number;
		slug: string;
		title: string;
		author: string;
		coverUrl: string | null;
		genres: string[];
		avgRating?: number;
	}

	interface Props {
		books: BookCardData[];
	}
	let { books }: Props = $props();
</script>

<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
	{#each books as book (book.id)}
		<BookCard {...book} />
	{/each}
</div>
