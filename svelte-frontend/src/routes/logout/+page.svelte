<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Card } from '$lib/components/ui/card';
</script>

<svelte:head>
	<title>Sign out — Storyshelf</title>
</svelte:head>

<div class="max-w-md mx-auto px-6 py-16">
	<Card class="p-6 text-center space-y-4">
		<h1 class="font-display text-2xl font-medium text-ink">Sign out</h1>
		<p class="text-sm text-muted">Are you sure you want to sign out?</p>
		<form method="POST">
			<Button type="submit" class="w-full">Sign out</Button>
		</form>
	</Card>
</div>
