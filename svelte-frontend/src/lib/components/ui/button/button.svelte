<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
		size?: 'default' | 'sm' | 'lg' | 'icon';
		class?: string;
		href?: string;
		children: import('svelte').Snippet;
		disabled?: boolean;
		type?: 'button' | 'submit' | 'reset';
		[key: string]: any;
	}

	let {
		variant = 'default',
		size = 'default',
		class: className = '',
		href = undefined,
		children,
		disabled = false,
		type = 'button' as const,
		...restProps
	}: Props = $props();

	const base =
		'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ink/20 disabled:pointer-events-none disabled:opacity-50';

	const variants: Record<string, string> = {
		default: 'bg-accent text-white hover:bg-accent-hover shadow-sm',
		destructive: 'bg-danger text-white hover:opacity-90 shadow-sm',
		outline: 'border border-rule bg-surface hover:bg-paper-2 text-ink shadow-sm',
		secondary: 'bg-paper-2 text-ink hover:bg-rule',
		ghost: 'hover:bg-paper-2 text-ink',
		link: 'text-accent underline-offset-4 hover:underline'
	};

	const sizes: Record<string, string> = {
		default: 'h-9 px-4 py-2',
		sm: 'h-8 rounded-md px-3 text-xs',
		lg: 'h-10 rounded-md px-8',
		icon: 'h-9 w-9'
	};
</script>

{#if href}
	<a {href} class={cn(base, variants[variant], sizes[size], className)} {...restProps}>
		{@render children()}
	</a>
{:else}
	<button
		{type}
		{disabled}
		class={cn(base, variants[variant], sizes[size], className)}
		{...restProps}
	>
		{@render children()}
	</button>
{/if}
