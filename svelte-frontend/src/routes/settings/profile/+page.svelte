<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Switch } from '$lib/components/ui/switch';
	import { Card } from '$lib/components/ui/card';
	import { enhance } from '$app/forms';

	interface Props {
		data?: Record<string, unknown>;
		form?: Record<string, unknown>;
	}
	let { data, form }: Props = $props();
</script>

<svelte:head>
	<title>Profile & Privacy — Storyshelf</title>
</svelte:head>

<div class="space-y-8">
	<!-- Toggles -->
	<Card class="p-5">
		<h2 class="font-sans text-base font-semibold text-ink mb-4">Privacy settings</h2>
		<form method="POST" action="?/privacy" use:enhance class="space-y-4">
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm font-medium text-ink">Show real name</p>
					<p class="text-xs text-muted">Display your real name on your profile.</p>
				</div>
				<Switch name="show_real_name" />
			</div>
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm font-medium text-ink">Activity feed</p>
					<p class="text-xs text-muted">Show your reading activity to others.</p>
				</div>
				<Switch name="show_activity" />
			</div>
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm font-medium text-ink">AI learning</p>
					<p class="text-xs text-muted">Allow AI to learn from your notes and reviews.</p>
				</div>
				<Switch name="ai_learn_from_notes" />
			</div>
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm font-medium text-ink">Search engine indexing</p>
					<p class="text-xs text-muted">Allow search engines to index your profile.</p>
				</div>
				<Switch name="indexed_by_search_engines" />
			</div>
			<div class="flex justify-end">
				<Button size="sm" type="submit">Save changes</Button>
			</div>
		</form>
	</Card>
</div>
