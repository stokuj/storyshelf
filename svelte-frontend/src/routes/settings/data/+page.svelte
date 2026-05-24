<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Card } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { Separator } from '$lib/components/ui/separator';
	import { Download, Pause, Trash2 } from 'lucide-svelte';
	import { enhance } from '$app/forms';

	interface Props {
		data?: Record<string, unknown>;
		form?: Record<string, unknown>;
	}
	let { data, form }: Props = $props();

	let deleteHandle = $state('');
	let showDeleteDialog = $state(false);
</script>

<svelte:head>
	<title>Data & Export — Storyshelf</title>
</svelte:head>

<div class="space-y-8">
	<!-- Export -->
	<Card class="p-5">
		<h2 class="font-sans text-base font-semibold text-ink mb-2">Export your data</h2>
		<p class="text-sm text-ink-2 mb-4">
			Download all your books, reviews, notes, and AI extraction data in a portable format.
		</p>
		<form method="POST" action="?/export" use:enhance>
			<Button variant="outline" size="sm" type="submit">
				<Download class="mr-2 size-4" />
				Export all data
			</Button>
		</form>
	</Card>

	<!-- Pause account -->
	<Card class="p-5">
		<h2 class="font-sans text-base font-semibold text-ink mb-2">Pause account</h2>
		<p class="text-sm text-ink-2 mb-4">
			Your profile will be hidden and you won't receive notifications. You can reactivate
			anytime.
		</p>
		<form method="POST" action="?/pause" use:enhance>
			<Button variant="outline" size="sm" type="submit">
				<Pause class="mr-2 size-4" />
				Pause account
			</Button>
		</form>
	</Card>

	<Separator />

	<!-- Danger zone -->
	<Card class="p-5 border-danger/20">
		<h2 class="font-sans text-base font-semibold text-danger mb-2">Danger zone</h2>
		<p class="text-sm text-ink-2 mb-4">
			Permanently delete your account and all associated data. This action is irreversible.
		</p>

		<Button
			variant="outline"
			size="sm"
			class="border-danger text-danger hover:bg-danger/10"
			onclick={() => (showDeleteDialog = true)}
		>
			<Trash2 class="mr-2 size-4" />
			Delete account
		</Button>

		{#if showDeleteDialog}
			<!-- Inline dialog overlay -->
			<div
				class="fixed inset-0 z-50 flex items-center justify-center"
				role="dialog"
				aria-modal="true"
			>
				<!-- svelte-ignore a11y_click_events_have_key_events -->
				<!-- svelte-ignore a11y_click_events_have_key_events -->
				<div
					class="fixed inset-0 bg-ink/50"
					role="presentation"
					onclick={() => (showDeleteDialog = false)}
				></div>
				<div
					class="relative z-50 rounded-lg border border-rule bg-surface p-6 shadow-lg max-w-lg w-full mx-4"
				>
					<h2 class="font-sans text-base font-semibold text-danger mb-2">
						Delete your account?
					</h2>
					<p class="text-sm text-ink-2 mb-4">
						This will permanently delete your account, all your data, and cannot be
						undone.
						Type <strong class="text-ink">your handle</strong> to confirm.
					</p>
					<form method="POST" action="?/delete" use:enhance class="space-y-3">
						<Input
							name="confirm"
							placeholder="Type your handle..."
							bind:value={deleteHandle}
							required
						/>
						<div class="flex justify-end gap-2">
							<Button
								variant="ghost"
								size="sm"
								onclick={() => (showDeleteDialog = false)}
							>
								Cancel
							</Button>
							<Button
								variant="outline"
								size="sm"
								class="border-danger text-danger"
								type="submit"
							>
								Delete my account
							</Button>
						</div>
					</form>
				</div>
			</div>
		{/if}
	</Card>
</div>
