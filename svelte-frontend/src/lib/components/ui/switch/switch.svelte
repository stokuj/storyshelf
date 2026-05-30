<script lang="ts">
	import { cn } from '$lib/utils';
	interface Props {
		class?: string;
		checked?: boolean;
		name?: string;
		disabled?: boolean;
		[key: string]: any;
	}
	let {
		class: className = '',
		checked = $bindable(false),
		name,
		disabled = false,
		...restProps
	}: Props = $props();
</script>

<button
	type="button"
	role="switch"
	aria-checked={checked}
	{disabled}
	onclick={() => (checked = !checked)}
	class={cn(
		'peer inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:cursor-not-allowed disabled:opacity-50',
		checked ? 'bg-accent' : 'bg-rule',
		className
	)}
	{...restProps}
>
	<span
		class={cn(
			'pointer-events-none block size-4 rounded-full bg-white shadow-lg ring-0 transition-transform',
			checked ? 'translate-x-4' : 'translate-x-0'
		)}
	></span>
</button>
<!-- Hidden checkbox so the switch submits its value in a plain form POST. -->
{#if name}
	<input type="checkbox" {name} bind:checked {disabled} hidden />
{/if}
