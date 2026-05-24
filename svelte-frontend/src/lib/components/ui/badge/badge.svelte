<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		variant?: 'default' | 'secondary' | 'outline' | 'destructive';
		class?: string;
		children: import('svelte').Snippet;
		[key: string]: any;
	}

	let { variant = 'default', class: className = '', children, ...restProps }: Props = $props();

	const base =
		'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2';

	const variants: Record<string, string> = {
		default: 'border-transparent bg-accent text-white shadow hover:bg-accent-hover',
		secondary: 'border-transparent bg-paper-2 text-ink-2 hover:bg-rule',
		outline: 'border-rule text-ink',
		destructive: 'border-transparent bg-danger text-white shadow hover:opacity-90'
	};
</script>

<span class={cn(base, variants[variant], className)} {...restProps}>
	{@render children()}
</span>
