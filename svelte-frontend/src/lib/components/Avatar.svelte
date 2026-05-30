<script lang="ts">
	interface Props {
		name: string;
		avatarUrl?: string | null;
		size?: 'sm' | 'md' | 'lg' | 'xl';
	}
	let { name, avatarUrl = null, size = 'md' }: Props = $props();

	const sizeClasses: Record<string, string> = {
		sm: 'size-8 text-xs',
		md: 'size-10 text-sm',
		lg: 'size-14 text-base',
		xl: 'size-20 text-lg'
	};

	function initials(n: string): string {
		return n
			.split(' ')
			.slice(0, 2)
			.map((p) => p[0])
			.join('')
			.toUpperCase();
	}
</script>

<div
	class="relative {sizeClasses[
		size
	]} rounded-full overflow-hidden border border-rule bg-paper-2 flex items-center justify-center"
>
	{#if avatarUrl}
		<img src={avatarUrl} alt={name} class="absolute inset-0 w-full h-full object-cover" />
	{:else}
		<span class="font-sans font-medium text-muted">{initials(name)}</span>
	{/if}
</div>
