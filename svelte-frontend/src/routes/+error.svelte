<script lang="ts">
	import { page } from '$app/stores';
	import { resolve } from '$app/paths';
</script>

<div class="flex min-h-screen items-center justify-center bg-gray-50 p-8">
	<div class="max-w-md text-center">
		<h1 class="mb-4 text-6xl font-bold text-gray-300">{$page.status}</h1>
		<p class="mb-8 text-lg text-gray-600">{$page.error?.message || 'Something went wrong'}</p>
		<a
			href={resolve('/')}
			class="rounded-lg bg-indigo-600 px-6 py-3 text-white hover:bg-indigo-700"
		>
			Go home
		</a>
	</div>
</div>
