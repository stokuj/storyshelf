<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Card } from '$lib/components/ui/card';
	import { enhance } from '$app/forms';
	import { resolve } from '$app/paths';

	interface Props {
		data?: { email?: string; error?: string; missing?: string };
	}
	let { data }: Props = $props();
</script>

<svelte:head>
	<title>Sign in — Storyshelf</title>
</svelte:head>

<div class="max-w-md mx-auto px-6 py-16">
	<Card class="p-6">
		<h1 class="font-display text-2xl font-medium text-ink mb-6 text-center">Sign in</h1>

		<form method="POST" use:enhance class="space-y-4">
			<div class="space-y-1.5">
				<Label for="email">Email</Label>
				<Input
					id="email"
					name="email"
					type="email"
					required
					value={data?.email ?? ''}
					class={data?.missing === 'email' ? 'border-danger' : ''}
				/>
			</div>

			<div class="space-y-1.5">
				<Label for="password">Password</Label>
				<Input
					id="password"
					name="password"
					type="password"
					required
					class={data?.missing === 'password' ? 'border-danger' : ''}
				/>
			</div>

			{#if data?.error}
				<p class="text-sm text-danger">{data.error}</p>
			{/if}

			<Button type="submit" class="w-full">Sign in</Button>
		</form>

		<p class="text-sm text-muted text-center mt-4">
			Don't have an account? <a href={resolve('/signup')} class="text-accent hover:underline"
				>Sign up</a
			>
		</p>
	</Card>
</div>
