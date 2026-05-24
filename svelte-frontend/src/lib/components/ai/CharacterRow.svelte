<script lang="ts">
	import CharacterAvatar from '$lib/components/character/CharacterAvatar.svelte';
	import AIBadge from './AIBadge.svelte';
	import {
		DropdownMenu,
		DropdownMenuContent,
		DropdownMenuItem,
		DropdownMenuTrigger
	} from '$lib/components/ui/dropdown-menu';
	import { MoreVertical, Check, X } from 'lucide-svelte';
	import { verifyCharacter, rejectCharacter } from '$lib/api/ai';
	import { toast } from 'svelte-sonner';
	import type { Character } from '$lib/types';

	interface Props {
		character: Character;
		bookId: number;
	}
	let { character, bookId }: Props = $props();

	let manuallyVerified = $state(false);
	let verified = $derived(manuallyVerified || character.source === 'ai-verified');

	async function handleVerify() {
		const { error } = await verifyCharacter(fetch, bookId, character.id);
		if (error) {
			toast.error('Failed to verify');
			return;
		}
		manuallyVerified = true;
		toast.success('Character verified');
	}

	async function handleReject() {
		const { error } = await rejectCharacter(fetch, bookId, character.id);
		if (error) {
			toast.error('Failed to reject');
			return;
		}
		toast.success('Character rejected');
	}
</script>

<div class="flex items-center gap-2.5 py-1">
	<CharacterAvatar name={character.name} size="sm" />
	<div class="flex-1 min-w-0">
		<div class="flex items-center gap-1.5">
			<span class="text-sm font-medium text-ink truncate">{character.name}</span>
			{#if character.source === 'ai' && !verified}
				<AIBadge />
			{/if}
		</div>
		<span class="text-xs text-muted">{character.role}</span>
	</div>

	{#if character.source === 'ai' && !verified}
		<DropdownMenu>
			<DropdownMenuTrigger
				class="inline-flex items-center justify-center size-7 hover:bg-paper-2 rounded-md transition-colors"
				type="button"
			>
				<MoreVertical class="size-3.5" />
			</DropdownMenuTrigger>
			<DropdownMenuContent align="end">
				<DropdownMenuItem onclick={handleVerify}>
					<Check class="mr-2 size-3.5" /> Verify
				</DropdownMenuItem>
				<DropdownMenuItem onclick={handleReject}>
					<X class="mr-2 size-3.5" /> Reject
				</DropdownMenuItem>
			</DropdownMenuContent>
		</DropdownMenu>
	{/if}
</div>
