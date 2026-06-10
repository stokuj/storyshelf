<script lang="ts">
	import type { CharacterRelation } from '$lib/types/character';
	import { initials, monogramColor } from '$lib/utils/monogram';

	let {
		centerName,
		bookSlug,
		relations
	}: { centerName: string; bookSlug: string; relations: CharacterRelation[] } = $props();

	// Colour per relation group (matches the approved mockup).
	const GROUP_COLORS: Record<string, string> = {
		family: '#d97706',
		romance: '#db2777',
		friendship: '#16a34a',
		mentorship: '#2563eb',
		power: '#7c3aed',
		conflict: '#dc2626',
		other: '#6b7280'
	};
	const groupColor = (g: string) => GROUP_COLORS[g] ?? GROUP_COLORS.other;

	const W = 360;
	const H = 360;
	const CX = W / 2;
	const CY = H / 2;
	const R = 130;

	type Pill = { type: string; type_display: string; group: string };
	type Related = { to_slug: string; to_name: string; pills: Pill[] };

	// One node per related character; collect every relation type pointing to it.
	const characters = $derived.by(() => {
		// eslint-disable-next-line svelte/prefer-svelte-reactivity
		const map = new Map<string, Related>();
		for (const rel of relations) {
			let entry = map.get(rel.to_slug);
			if (!entry) {
				entry = { to_slug: rel.to_slug, to_name: rel.to_name, pills: [] };
				map.set(rel.to_slug, entry);
			}
			entry.pills.push({ type: rel.type, type_display: rel.type_display, group: rel.group });
		}
		return [...map.values()];
	});

	const nodes = $derived(
		characters.map((c, i) => {
			const angle = (2 * Math.PI * i) / Math.max(characters.length, 1) - Math.PI / 2;
			return { c, x: CX + R * Math.cos(angle), y: CY + R * Math.sin(angle) };
		})
	);

	// Groups present in this graph, for the legend.
	const legendGroups = $derived([...new Set(relations.map((r) => r.group))]);
</script>

{#if relations.length === 0}
	<p class="text-sm text-muted">No relations recorded.</p>
{:else}
	<svg
		viewBox="0 0 {W} {H}"
		role="img"
		aria-label="Relation graph"
		class="w-full max-w-md rounded-xl border border-rule bg-surface"
	>
		{#each nodes as node (node.c.to_slug)}
			<line x1={CX} y1={CY} x2={node.x} y2={node.y} stroke="#8884" stroke-width="2" />
		{/each}

		{#each nodes as node (node.c.to_slug)}
			{#each node.c.pills as pill, j (`${node.c.to_slug}::${pill.type}`)}
				{@const mx = (CX + node.x) / 2}
				{@const my = (CY + node.y) / 2 + (j - (node.c.pills.length - 1) / 2) * 20}
				{@const w = pill.type_display.length * 6.6 + 16}
				<rect
					x={mx - w / 2}
					y={my - 9}
					width={w}
					height="18"
					rx="9"
					fill={groupColor(pill.group)}
				/>
				<text x={mx} y={my + 4} fill="#fff" font-size="11" text-anchor="middle">
					{pill.type_display}
				</text>
			{/each}
		{/each}

		{#each nodes as node (node.c.to_slug)}
			<a href="/books/{bookSlug}/characters/{node.c.to_slug}" aria-label={node.c.to_name}>
				<circle cx={node.x} cy={node.y} r="26" fill={monogramColor(node.c.to_name)} />
				<text x={node.x} y={node.y + 4} fill="#fff" font-size="12" text-anchor="middle">
					{initials(node.c.to_name)}
				</text>
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
		<text x={CX} y={CY + 5} fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">
			{initials(centerName)}
		</text>
	</svg>

	<div class="mt-3 flex flex-wrap gap-2">
		{#each legendGroups as g (g)}
			<span
				class="rounded-full px-3 py-1 text-xs capitalize text-white"
				style="background:{groupColor(g)}"
			>
				{g}
			</span>
		{/each}
	</div>
{/if}
