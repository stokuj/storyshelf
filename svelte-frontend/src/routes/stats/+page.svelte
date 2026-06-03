<script lang="ts">
	import { Card } from '$lib/components/ui/card';
	import BarChart from '$lib/components/stats/BarChart.svelte';
	import type { UserStats } from '$lib/api/stats';

	let { data }: { data: { stats: UserStats } } = $props();
	const stats = $derived(data.stats);

	const yearBars = $derived(
		stats.books_per_year.map((y) => ({ label: String(y.year), value: y.count }))
	);
	const ratingBars = $derived(
		stats.rating_distribution.map((r) => ({ label: `${r.rating}★`, value: r.count }))
	);
</script>

<svelte:head>
	<title>Reading Stats — Storyshelf</title>
</svelte:head>

<div class="max-w-[1240px] mx-auto px-6 md:px-10 py-8 space-y-8">
	<h1 class="font-display text-2xl font-semibold text-ink">Reading stats</h1>

	<!-- Status counts -->
	<div class="grid grid-cols-3 gap-4">
		<Card class="p-5 text-center">
			<div class="text-2xl font-semibold text-ink">{stats.status_counts.want_to_read}</div>
			<div class="text-xs text-muted mt-1">Want to read</div>
		</Card>
		<Card class="p-5 text-center">
			<div class="text-2xl font-semibold text-ink">{stats.status_counts.reading}</div>
			<div class="text-xs text-muted mt-1">Reading</div>
		</Card>
		<Card class="p-5 text-center">
			<div class="text-2xl font-semibold text-ink">{stats.status_counts.read}</div>
			<div class="text-xs text-muted mt-1">Read</div>
		</Card>
	</div>

	<!-- Totals -->
	<div class="grid grid-cols-3 gap-4">
		<Card class="p-5 text-center">
			<div class="text-2xl font-semibold text-ink">{stats.totals.pages_read}</div>
			<div class="text-xs text-muted mt-1">Pages read</div>
		</Card>
		<Card class="p-5 text-center">
			<div class="text-2xl font-semibold text-ink">
				{stats.totals.avg_rating_given ?? '—'}
			</div>
			<div class="text-xs text-muted mt-1">Avg rating given</div>
		</Card>
		<Card class="p-5 text-center">
			<div class="text-2xl font-semibold text-ink">
				{stats.time_on_shelf_days ?? '—'}
			</div>
			<div class="text-xs text-muted mt-1">Avg days on shelf</div>
		</Card>
	</div>

	<!-- Books per year -->
	<Card class="p-5">
		<h2 class="font-sans text-base font-semibold text-ink mb-4">Books read per year</h2>
		<BarChart bars={yearBars} ariaLabel="Books read per year" />
	</Card>

	<!-- Rating distribution -->
	<Card class="p-5">
		<h2 class="font-sans text-base font-semibold text-ink mb-4">Your ratings</h2>
		<BarChart bars={ratingBars} ariaLabel="Rating distribution" />
	</Card>
</div>
