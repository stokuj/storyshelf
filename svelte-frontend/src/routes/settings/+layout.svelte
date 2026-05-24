<script lang="ts">
	import { page } from '$app/stores';
	import { User, Shield, Bell, Sparkles, Database } from 'lucide-svelte';
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}
	let { children }: Props = $props();

	const navItems = [
		{ label: 'Account', href: '/settings', icon: User },
		{ label: 'Profile & privacy', href: '/settings/profile', icon: Shield },
		{ label: 'Notifications', href: '/settings/notifications', icon: Bell },
		{ label: 'AI preferences', href: '/settings/ai', icon: Sparkles },
		{ label: 'Data & export', href: '/settings/data', icon: Database }
	];
</script>

<div class="max-w-[1240px] mx-auto px-6 md:px-10 py-8">
	<h1 class="font-display text-3xl font-medium text-ink mb-8">Settings</h1>

	<div class="grid grid-cols-1 md:grid-cols-[220px_1fr] gap-8">
		<!-- Left rail -->
		<nav class="space-y-1">
			{#each navItems as item}
				<a
					href={item.href}
					class="flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-colors"
					class:bg-ink={$page.url.pathname === item.href}
					class:text-paper={$page.url.pathname === item.href}
					class:text-ink-2={$page.url.pathname !== item.href}
					class:hover:bg-paper-2={$page.url.pathname !== item.href}
				>
					<item.icon class="size-4" />
					{item.label}
				</a>
			{/each}
		</nav>

		<!-- Content -->
		<div class="min-w-0">
			{@render children()}
		</div>
	</div>
</div>
