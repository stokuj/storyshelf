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
	<title>Notifications — Storyshelf</title>
</svelte:head>

<div class="space-y-8">
	<Card class="p-5">
		<h2 class="font-sans text-base font-semibold text-ink mb-4">Email notifications</h2>
		<form method="POST" action="?/email" use:enhance class="space-y-4">
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm font-medium text-ink">New followers</p>
					<p class="text-xs text-muted">When someone follows you.</p>
				</div>
				<Switch name="notify_followers" />
			</div>
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm font-medium text-ink">Book recommendations</p>
					<p class="text-xs text-muted">Weekly book picks based on your shelves.</p>
				</div>
				<Switch name="notify_recommendations" />
			</div>
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm font-medium text-ink">AI extraction complete</p>
					<p class="text-xs text-muted">When a character extraction finishes.</p>
				</div>
				<Switch name="notify_ai" />
			</div>
			<div class="flex justify-end">
				<Button size="sm" type="submit">Save</Button>
			</div>
		</form>
	</Card>

	<Card class="p-5">
		<h2 class="font-sans text-base font-semibold text-ink mb-4">Push notifications</h2>
		<form method="POST" action="?/push" use:enhance class="space-y-4">
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm font-medium text-ink">Enable push notifications</p>
					<p class="text-xs text-muted">Receive notifications in your browser.</p>
				</div>
				<Switch name="push_enabled" />
			</div>
			<div class="flex justify-end">
				<Button size="sm" type="submit">Save</Button>
			</div>
		</form>
	</Card>
</div>
