<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { Input } from '$lib/components/ui/input';
	import { Users } from 'lucide-svelte';

	let value = $derived($page.url.searchParams.get('character') ?? '');

	let debounceTimer: ReturnType<typeof setTimeout>;

	function onInput(e: Event) {
		clearTimeout(debounceTimer);
		const input = (e.target as HTMLInputElement).value;
		debounceTimer = setTimeout(() => {
			const url = new URL($page.url);
			if (input) {
				url.searchParams.set('character', input);
			} else {
				url.searchParams.delete('character');
			}
			url.searchParams.delete('page');
			goto(url, { keepFocus: true });
		}, 300);
	}
</script>

<div class="relative w-full max-w-xs">
	<Users class="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted" />
	<Input class="pl-8" placeholder="Contains character…" {value} oninput={onInput} />
</div>
