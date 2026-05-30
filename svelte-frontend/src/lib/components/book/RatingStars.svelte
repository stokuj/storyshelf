<script lang="ts">
	import { Star } from 'lucide-svelte';

	interface Props {
		rating?: number | null;
		onRate?: (rating: number) => Promise<void>;
		readonly?: boolean;
		size?: 'sm' | 'md';
	}

	let { rating = null, onRate = undefined, readonly = false, size = 'md' }: Props = $props();

	const sizeCls = $derived(size === 'sm' ? 'size-3' : 'size-4');
	let hoverValue = $state(0);
	let loading = $state(false);

	const displayValue = $derived(hoverValue > 0 ? hoverValue : (rating ?? 0));

	async function handleClick(star: number) {
		if (readonly || loading || !onRate) return;
		loading = true;
		try {
			await onRate(star);
		} finally {
			loading = false;
		}
	}
</script>

<div class="inline-flex items-center gap-0.5">
	{#each [1, 2, 3, 4, 5] as star (star)}
		<button
			type="button"
			data-testid="rating-star"
			data-rating={star}
			data-selected={star <= (rating ?? 0)}
			class="transition-transform {readonly || !onRate
				? 'cursor-default'
				: 'cursor-pointer hover:scale-110'}"
			class:text-accent={star <= displayValue}
			class:text-rule={star > displayValue}
			disabled={readonly || loading}
			aria-label="{star} star{star > 1 ? 's' : ''}"
			onclick={() => handleClick(star)}
			onmouseenter={() => {
				if (!readonly && !loading && onRate) hoverValue = star;
			}}
			onmouseleave={() => {
				hoverValue = 0;
			}}
		>
			<Star class={sizeCls} fill={star <= displayValue ? 'currentColor' : 'none'} />
		</button>
	{/each}
</div>
