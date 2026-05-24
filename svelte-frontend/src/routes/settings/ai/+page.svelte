<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import {
		Select,
		SelectTrigger,
		SelectValue,
		SelectContent,
		SelectItem
	} from '$lib/components/ui/select';
	import { Card } from '$lib/components/ui/card';
	import { enhance } from '$app/forms';

	// eslint-disable-next-line no-empty-pattern
	let {} = $props();
</script>

<svelte:head>
	<title>AI Preferences — Storyshelf</title>
</svelte:head>

<div class="space-y-8">
	<Card class="p-5">
		<h2 class="font-sans text-base font-semibold text-ink mb-4">AI assistant preferences</h2>
		<form method="POST" action="?/ai" use:enhance class="space-y-4">
			<div class="space-y-1.5">
				<span class="text-sm font-medium text-ink">Tone</span>
				<Select>
					<SelectTrigger>
						<SelectValue placeholder="Scholarly" />
					</SelectTrigger>
					<SelectContent>
						<SelectItem value="scholarly">Scholarly</SelectItem>
						<SelectItem value="casual">Casual</SelectItem>
						<SelectItem value="concise">Concise</SelectItem>
					</SelectContent>
				</Select>
			</div>

			<div class="space-y-1.5">
				<span class="text-sm font-medium text-ink">Default spoiler limit</span>
				<Select>
					<SelectTrigger>
						<SelectValue placeholder="Current chapter" />
					</SelectTrigger>
					<SelectContent>
						<SelectItem value="current-chapter">Current chapter</SelectItem>
						<SelectItem value="whole-book">Whole book</SelectItem>
						<SelectItem value="no-limit">No limit</SelectItem>
					</SelectContent>
				</Select>
			</div>

			<div class="space-y-1.5">
				<span class="text-sm font-medium text-ink">Cite quotes</span>
				<Select>
					<SelectTrigger>
						<SelectValue placeholder="Always" />
					</SelectTrigger>
					<SelectContent>
						<SelectItem value="always">Always</SelectItem>
						<SelectItem value="on-request">On request</SelectItem>
						<SelectItem value="never">Never</SelectItem>
					</SelectContent>
				</Select>
			</div>

			<div class="flex justify-end">
				<Button size="sm" type="submit">Save</Button>
			</div>
		</form>
	</Card>
</div>
