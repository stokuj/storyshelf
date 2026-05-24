<script lang="ts">
	interface Props {
		coverUrl: string | null;
		title: string;
		size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
	}
	let { coverUrl, title, size = 'md' }: Props = $props();

	const sizeClasses: Record<string, string> = {
		xs: 'w-[48px]',
		sm: 'w-[72px]',
		md: 'w-[112px]',
		lg: 'w-[180px]',
		xl: 'w-[260px]'
	};
</script>

<div
	class="relative aspect-[2/3] {sizeClasses[
		size
	]} overflow-hidden rounded-md border border-rule bg-paper-2"
>
	{#if coverUrl}
		<img
			src={coverUrl}
			alt={title}
			loading="lazy"
			class="absolute inset-0 w-full h-full object-cover"
		/>
	{:else}
		<div class="absolute inset-0 flex items-center justify-center p-3">
			<span class="font-display text-sm text-muted text-center leading-tight">{title}</span>
		</div>
	{/if}
</div>
