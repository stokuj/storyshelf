<script lang="ts">
	let { data } = $props();
</script>

<main style="font-family: sans-serif; padding: 2rem;">
	{#if data.user}
		<h1>Hello, {data.user.display_name || data.user.handle}!</h1>
		<p>Email: {data.user.email}</p>
		<p>Profile public: {data.user.settings.profile_public}</p>
	{:else}
		<h1>StoryShelf</h1>
		<p>Not logged in. Log in page coming in Phase 2.7.</p>
	{/if}
</main>
