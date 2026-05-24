<script lang="ts">
	interface Props {
		kind: 'family' | 'romance' | 'ally' | 'enemy' | 'rival' | 'mentor' | 'other';
		label: string;
	}
	let { kind, label }: Props = $props();

	const colorMap: Record<string, string> = {
		family: 'bg-rel-family/15 text-rel-family',
		romance: 'bg-rel-romance/15 text-rel-romance',
		ally: 'bg-rel-ally/15 text-rel-ally',
		enemy: 'bg-rel-enemy/15 text-rel-enemy',
		rival: 'bg-rel-enemy/15 text-rel-enemy',
		mentor: 'bg-rel-ally/15 text-rel-ally',
		other: 'bg-muted/15 text-muted'
	};
</script>

<span
	class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-pill text-xs font-medium {colorMap[
		kind
	] ?? 'bg-muted/15 text-muted'}"
>
	<span class="inline-block size-1.5 rounded-full bg-current"></span>
	{label}
</span>
