<script lang="ts">
	import { Toaster as Sonner } from 'svelte-sonner';

	interface Props {
		class?: string;
		[key: string]: any;
	}

	let { class: className = '', ...restProps }: Props = $props();
</script>

<Sonner
	class={className}
	toastOptions={{ classes: { toast: 'bg-surface text-ink border border-rule shadow-md' } }}
	{...restProps}
/>
