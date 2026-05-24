<script lang="ts">
	import { Star } from 'lucide-svelte';

	interface Props {
		value?: number;
		readonly?: boolean;
		size?: 'sm' | 'md';
	}
	let { value = $bindable(0), readonly = false, size = 'md' }: Props = $props();

	const sizeMap: Record<string, string> = { sm: 'size-3', md: 'size-4' };
	const sizeCls = $derived(sizeMap[size] ?? 'size-4');

	let hoverValue = $state(0);

	function handleClick(star: number) {
		if (!readonly) {
			value = star;
		}
	}
</script>

<div class="inline-flex items-center gap-0.5">
	{#each [1, 2, 3, 4, 5] as star}
		<button
			type="button"
			class="transition-colors {readonly ? 'cursor-default' : 'cursor-pointer hover:scale-110 transition-transform'}"
			class:text-accent={star <= value || star <= hoverValue}
			class:text-rule={star > value && star > hoverValue}
			disabled={readonly}
			onclick={() => handleClick(star)}
			onmouseenter={() => {
				if (!readonly) hoverValue = star;
			}}
			onmouseleave={() => {
				hoverValue = 0;
			}}
			aria-label="{star} star{star > 1 ? 's' : ''}"
		>
			<Star
				class={sizeCls}
				fill={(star <= value || star <= hoverValue) ? 'currentColor' : 'none'}
			/>
		</button>
	{/each}
</div>
