<script lang="ts">
	import { ChevronDown } from 'lucide-svelte';
	import type { ShelfStatus } from '$lib/types/shelf';

	interface Props {
		currentStatus: ShelfStatus;
		onChange: (status: ShelfStatus) => Promise<void> | void;
		disabled?: boolean;
	}

	let { currentStatus, onChange, disabled = false }: Props = $props();

	const options: { value: ShelfStatus; label: string; color: string }[] = [
		{ value: 'WANT_TO_READ', label: 'Want to Read', color: 'text-info' },
		{ value: 'READING', label: 'Reading', color: 'text-warning' },
		{ value: 'READ', label: 'Read', color: 'text-success' }
	];

	let open = $state(false);
	let loading = $state(false);
	const current = $derived(options.find((o) => o.value === currentStatus));

	async function select(value: ShelfStatus) {
		if (disabled || loading || value === currentStatus) {
			open = false;
			return;
		}
		open = false;
		loading = true;
		try {
			await onChange(value);
		} finally {
			loading = false;
		}
	}
</script>

<svelte:window onkeydown={(e) => e.key === 'Escape' && (open = false)} />

<div class="relative">
	<button
		type="button"
		data-testid="status-dropdown"
		class="flex items-center justify-between gap-1.5 w-full rounded-md border border-rule bg-surface px-2.5 py-1.5 text-xs font-medium transition-colors hover:bg-paper-2 disabled:opacity-50 {current?.color ??
			''}"
		disabled={disabled || loading}
		aria-haspopup="listbox"
		aria-expanded={open}
		onclick={() => (open = !open)}
	>
		<span>{current?.label ?? currentStatus}</span>
		<ChevronDown class="size-3 text-muted transition-transform {open ? 'rotate-180' : ''}" />
	</button>

	{#if open}
		<div
			class="absolute top-full left-0 right-0 mt-1 z-20 rounded-md border border-rule bg-surface shadow-lg py-1"
			role="listbox"
		>
			{#each options as opt (opt.value)}
				<button
					type="button"
					role="option"
					aria-selected={opt.value === currentStatus}
					class="w-full text-left px-2.5 py-1.5 text-xs font-medium hover:bg-paper-2 {opt.color} {opt.value ===
					currentStatus
						? 'font-semibold'
						: ''}"
					onclick={() => select(opt.value)}
				>
					{opt.label}
				</button>
			{/each}
		</div>
		<button
			type="button"
			class="fixed inset-0 z-10"
			aria-label="Close menu"
			tabindex="-1"
			onclick={() => (open = false)}
		></button>
	{/if}
</div>
