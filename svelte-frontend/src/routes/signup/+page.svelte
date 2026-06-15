<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Card } from '$lib/components/ui/card';
	import { enhance } from '$app/forms';
	import { resolve } from '$app/paths';

	interface Props {
		form?: {
			email?: string;
			handle?: string;
			error?: string;
			errors?: Record<string, string>;
		};
	}
	// Action results (validation/errors) arrive via `form`, not `data`.
	let { form }: Props = $props();
</script>

<svelte:head>
	<title>Sign up — Storyshelf</title>
</svelte:head>

<div class="max-w-md mx-auto px-6 py-16">
	<Card class="p-6">
		<h1 class="font-display text-2xl font-medium text-ink mb-6 text-center">Create an account</h1>

		<form method="POST" use:enhance class="space-y-4">
			<div class="space-y-1.5">
				<Label for="email">Email</Label>
				<Input
					id="email"
					name="email"
					type="email"
					required
					value={form?.email ?? ''}
					class={form?.errors?.email ? 'border-danger' : ''}
				/>
				{#if form?.errors?.email}
					<p class="text-xs text-danger">{form.errors.email}</p>
				{/if}
			</div>

			<div class="space-y-1.5">
				<Label for="handle">Handle</Label>
				<Input
					id="handle"
					name="handle"
					type="text"
					required
					value={form?.handle ?? ''}
					class={form?.errors?.handle ? 'border-danger' : ''}
				/>
				{#if form?.errors?.handle}
					<p class="text-xs text-danger">{form.errors.handle}</p>
				{/if}
			</div>

			<div class="space-y-1.5">
				<Label for="password">Password</Label>
				<Input
					id="password"
					name="password"
					type="password"
					required
					class={form?.errors?.password ? 'border-danger' : ''}
				/>
				{#if form?.errors?.password}
					<p class="text-xs text-danger">{form.errors.password}</p>
				{/if}
			</div>

			{#if form?.error}
				<p class="text-sm text-danger">{form.error}</p>
			{/if}

			<Button type="submit" class="w-full">Create account</Button>
		</form>

		<p class="text-sm text-muted text-center mt-4">
			Already have an account? <a href={resolve('/login')} class="text-accent hover:underline"
				>Sign in</a
			>
		</p>
	</Card>
</div>
