<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Card } from '$lib/components/ui/card';
	import Avatar from '$lib/components/Avatar.svelte';
	import { enhance } from '$app/forms';
	import { page } from '$app/state';
	import type { UserMe } from '$lib/api/user';

	let user: UserMe | null | undefined = $derived(page.data.user as UserMe | null | undefined);

	// eslint-disable-next-line no-empty-pattern
	let {} = $props();
</script>

<svelte:head>
	<title>Account Settings — Storyshelf</title>
</svelte:head>

<div class="space-y-8">
	<!-- Avatar -->
	<Card class="p-5">
		<h2 class="font-sans text-base font-semibold text-ink mb-4">Avatar</h2>
		<div class="flex items-center gap-4">
			<Avatar name={user?.display_name ?? 'User'} avatarUrl={user?.avatar_url} size="xl" />
			<div>
				<form method="POST" action="?/avatar" enctype="multipart/form-data" use:enhance>
					<input
						type="file"
						name="avatar"
						accept="image/*"
						class="hidden"
						id="avatar-upload"
						onchange={(e) => e.currentTarget.form?.requestSubmit()}
					/>
					<Button
						variant="outline"
						size="sm"
						type="button"
						onclick={() => document.getElementById('avatar-upload')?.click()}
					>
						Upload photo
					</Button>
				</form>
				<p class="text-xs text-muted mt-1">JPG, PNG or GIF. Max 2MB.</p>
			</div>
		</div>
	</Card>

	<!-- Display name -->
	<Card class="p-5">
		<h2 class="font-sans text-base font-semibold text-ink mb-4">Display name</h2>
		<form method="POST" action="?/profile" use:enhance class="space-y-3">
			<Input name="display_name" value={user?.display_name ?? ''} placeholder="Your display name" />
			<div class="flex justify-end">
				<Button size="sm" type="submit">Save</Button>
			</div>
		</form>
	</Card>

	<!-- Handle -->
	<Card class="p-5">
		<h2 class="font-sans text-base font-semibold text-ink mb-4">Handle</h2>
		<form method="POST" action="?/handle" use:enhance class="space-y-3">
			<Input name="handle" value={user?.handle ?? ''} placeholder="your-handle" />
			<div class="flex justify-end">
				<Button size="sm" type="submit">Save</Button>
			</div>
		</form>
	</Card>

	<!-- Email -->
	<Card class="p-5">
		<h2 class="font-sans text-base font-semibold text-ink mb-4">Email</h2>
		<form method="POST" action="?/email" use:enhance class="space-y-3">
			<Input name="email" value={user?.email ?? ''} type="email" placeholder="you@example.com" />
			<div class="flex justify-end">
				<Button size="sm" type="submit">Change email</Button>
			</div>
		</form>
	</Card>

	<!-- Password -->
	<Card class="p-5">
		<h2 class="font-sans text-base font-semibold text-ink mb-4">Password</h2>
		<form method="POST" action="?/password" use:enhance class="space-y-3">
			<div class="space-y-1.5">
				<Label for="current">Current password</Label>
				<Input id="current" name="current_password" type="password" />
			</div>
			<div class="space-y-1.5">
				<Label for="new">New password</Label>
				<Input id="new" name="new_password" type="password" />
			</div>
			<div class="space-y-1.5">
				<Label for="confirm">Confirm new password</Label>
				<Input id="confirm" name="confirm_password" type="password" />
			</div>
			<!-- Simple password strength heuristic -->
			<div>
				<div class="w-full bg-rule rounded-full h-1.5">
					<div class="bg-accent rounded-full h-1.5" style="width: 25%"></div>
				</div>
				<p class="text-xs text-muted mt-1">Password strength: Weak</p>
			</div>
			<div class="flex justify-end">
				<Button size="sm" type="submit">Change password</Button>
			</div>
		</form>
	</Card>
</div>
