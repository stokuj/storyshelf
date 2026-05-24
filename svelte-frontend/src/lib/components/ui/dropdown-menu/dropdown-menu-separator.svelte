<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		[key: string]: any;
	}

	let { class: className = '', ...restProps }: Props = $props();
</script>

<hr class={cn('-mx-1 my-1 border-rule', className)} {...restProps} />
