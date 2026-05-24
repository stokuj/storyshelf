<script lang="ts">
	import { Skeleton } from '$lib/components/ui/skeleton';
</script>

<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
	<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
	{#each Array(10) as _, i (i)}
		<div class="space-y-2">
			<Skeleton class="aspect-[2/3] w-full rounded-md" />
			<Skeleton class="h-4 w-3/4" />
			<Skeleton class="h-3 w-1/2" />
		</div>
	{/each}
</div>
