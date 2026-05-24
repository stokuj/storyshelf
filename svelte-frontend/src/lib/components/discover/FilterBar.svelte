<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import {
		Select,
		SelectTrigger,
		SelectValue,
		SelectContent,
		SelectItem
	} from '$lib/components/ui/select';
	import { Input } from '$lib/components/ui/input';
	import { Search } from 'lucide-svelte';

	let currentQ = $derived($page.url.searchParams.get('q') ?? '');

	function updateParam(key: string, value: string) {
		const url = new URL($page.url);
		if (value) {
			url.searchParams.set(key, value);
		} else {
			url.searchParams.delete(key);
		}
		url.searchParams.delete('page');
		goto(url, { keepFocus: true });
	}
</script>

<div class="flex flex-wrap items-center gap-3 mb-8">
	<div class="relative flex-1 min-w-[200px] max-w-sm">
		<Search class="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted" />
		<Input
			class="pl-8"
			placeholder="Search books…"
			value={currentQ}
			oninput={(e: Event) => updateParam('q', (e.target as HTMLInputElement).value)}
		/>
	</div>

	<Select>
		<SelectTrigger class="w-[140px]">
			<SelectValue placeholder="Genre" />
		</SelectTrigger>
		<SelectContent>
			<SelectItem value="">All genres</SelectItem>
			<SelectItem value="Science Fiction">Science Fiction</SelectItem>
			<SelectItem value="Fantasy">Fantasy</SelectItem>
			<SelectItem value="Literary Fiction">Literary Fiction</SelectItem>
			<SelectItem value="Mystery">Mystery</SelectItem>
			<SelectItem value="Romance">Romance</SelectItem>
			<SelectItem value="Non-Fiction">Non-Fiction</SelectItem>
		</SelectContent>
	</Select>

	<Select>
		<SelectTrigger class="w-[140px]">
			<SelectValue placeholder="Sort" />
		</SelectTrigger>
		<SelectContent>
			<SelectItem value="title">Title</SelectItem>
			<SelectItem value="rating">Rating</SelectItem>
			<SelectItem value="recent">Recent</SelectItem>
		</SelectContent>
	</Select>
</div>
