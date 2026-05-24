<script lang="ts">
	import '../app.css';
	import { ModeWatcher } from 'mode-watcher';
	import { Toaster } from '$lib/components/ui/sonner';
	import AppShell from '$lib/components/shell/AppShell.svelte';

	let { children } = $props();
</script>

<ModeWatcher />
<Toaster />
<AppShell>{@render children()}</AppShell>
