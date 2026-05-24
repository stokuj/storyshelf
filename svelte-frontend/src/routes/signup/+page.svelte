<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Card } from '$lib/components/ui/card';
	import { enhance } from '$app/forms';
	import { resolve } from '$app/paths';

	interface Props {
		data?: {
			email?: string;
			handle?: string;
			error?: string;
			errors?: Record<string, string>;
		};
	}
	let { data }: Props = $props();
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
					value={data?.email ?? ''}
					class={data?.errors?.email ? 'border-danger' : ''}
				/>
				{#if data?.errors?.email}
					<p class="text-xs text-danger">{data.errors.email}</p>
				{/if}
			</div>

			<div class="space-y-1.5">
				<Label for="handle">Handle</Label>
				<Input
					id="handle"
					name="handle"
					type="text"
					required
					value={data?.handle ?? ''}
					class={data?.errors?.handle ? 'border-danger' : ''}
				/>
				{#if data?.errors?.handle}
					<p class="text-xs text-danger">{data.errors.handle}</p>
				{/if}
			</div>

			<div class="space-y-1.5">
				<Label for="password">Password</Label>
				<Input
					id="password"
					name="password"
					type="password"
					required
					class={data?.errors?.password ? 'border-danger' : ''}
				/>
				{#if data?.errors?.password}
					<p class="text-xs text-danger">{data.errors.password}</p>
				{/if}
			</div>

			{#if data?.error}
				<p class="text-sm text-danger">{data.error}</p>
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
