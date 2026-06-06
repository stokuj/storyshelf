<script lang="ts">
	import type { CharacterRelation } from '$lib/types/character';
	import { initials, monogramColor } from '$lib/utils/monogram';

	let {
		centerName,
		bookSlug,
		relations
	}: { centerName: string; bookSlug: string; relations: CharacterRelation[] } = $props();

	const W = 360;
	const H = 360;
	const CX = W / 2;
	const CY = H / 2;
	const R = 130;

	// Position each related node evenly around a circle.
	const nodes = $derived(
		relations.map((rel, i) => {
			const angle = (2 * Math.PI * i) / Math.max(relations.length, 1) - Math.PI / 2;
			return {
				rel,
				x: CX + R * Math.cos(angle),
				y: CY + R * Math.sin(angle)
			};
		})
	);
</script>

{#if relations.length === 0}
	<p class="text-sm text-muted">No relations recorded.</p>
{:else}
	<svg viewBox="0 0 {W} {H}" class="w-full max-w-md rounded-xl border border-rule bg-surface">
		{#each nodes as node (`${node.rel.to_slug}::${node.rel.label}`)}
			<line x1={CX} y1={CY} x2={node.x} y2={node.y} stroke="#8884" stroke-width="2" />
			<text
				x={(CX + node.x) / 2}
				y={(CY + node.y) / 2 - 4}
				fill="currentColor"
				class="text-muted"
				font-size="11"
				text-anchor="middle">{node.rel.label}</text
			>
		{/each}

		{#each nodes as node (`${node.rel.to_slug}::${node.rel.label}`)}
			<a href="/books/{bookSlug}/characters/{node.rel.to_slug}" aria-label={node.rel.to_name}>
				<circle cx={node.x} cy={node.y} r="26" fill={monogramColor(node.rel.to_name)} />
				<text x={node.x} y={node.y + 4} fill="#fff" font-size="12" text-anchor="middle"
					>{initials(node.rel.to_name)}</text
				>
			</a>
		{/each}

		<circle
			cx={CX}
			cy={CY}
			r="32"
			fill={monogramColor(centerName)}
			stroke="#fff"
			stroke-width="3"
		/>
		<text x={CX} y={CY + 5} fill="#fff" font-size="14" font-weight="bold" text-anchor="middle"
			>{initials(centerName)}</text
		>
	</svg>
{/if}
